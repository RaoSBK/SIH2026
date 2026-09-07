// ML Graph Component

const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

/* ---------------- Spring engine (for panning) ---------------- */
export class Spring {
  constructor(value, opts={}) {
    this.value = value;
    this.velocity = opts.velocity || 0;
    this.target = value;
    this.damping = opts.damping ?? 1.0;
    this.response = opts.response ?? 0.35;
    this.onUpdate = opts.onUpdate || (() => {});
    this.onSettle = opts.onSettle || (() => {});
    this._raf = null;
  }
  jump(v) { this.value = v; this.target = v; this.velocity = 0; this.onUpdate(this.value); }
  set(target, velocityBoost) {
    this.target = target;
    if (velocityBoost !== undefined) this.velocity = velocityBoost;
    if (reduced) { this.jump(target); this.onSettle(); return; }
    this._run();
  }
  _run() {
    if (this._raf) return;
    let last = performance.now();
    const step = (now) => {
      const dt = Math.min((now - last) / 1000, 0.032);
      last = now;
      const w = 2 * Math.PI / this.response;
      const F = -2 * this.damping * w * this.velocity - w * w * (this.value - this.target);
      this.velocity += F * dt;
      this.value += this.velocity * dt;
      this.onUpdate(this.value);
      if (Math.abs(this.value - this.target) < 0.05 && Math.abs(this.velocity) < 0.05) {
        this.value = this.target; this.onUpdate(this.value);
        this._raf = null;
        this.onSettle();
        return;
      }
      this._raf = requestAnimationFrame(step);
    };
    this._raf = requestAnimationFrame(step);
  }
}

/* ---------------- ML Graph Engine ---------------- */
export class MLGraph {
  constructor(svgId, viewportId, nodes, links, onSelectNode) {
    this.svgNS = "http://www.w3.org/2000/svg";
    this.svg = document.getElementById(svgId);
    this.viewport = document.getElementById(viewportId);
    this.onSelectNode = onSelectNode;
    
    this.nodes = nodes;
    this.links = links;
    
    // Process degrees for sizing
    this.degree = {};
    this.nodes.forEach(n => this.degree[n.id] = 0);
    this.links.forEach(e => {
      if(this.degree[e.source] !== undefined) this.degree[e.source]++;
      if(this.degree[e.target] !== undefined) this.degree[e.target]++;
    });

    this.nodeGroups = {};
    
    this.initLayout();
    this.initPanning();
  }

  el(tag, attrs) {
    const e = document.createElementNS(this.svgNS, tag);
    for (const k in attrs) e.setAttribute(k, attrs[k]);
    return e;
  }
  
  // Basic Circular Layout since ML nodes don't have x,y
  initLayout() {
    if (!this.nodes || this.nodes.length === 0) return;
    
    const width = 2400;
    const height = 1800;

    // Use D3 for live force layout instead of static iteration
    this.simulation = d3.forceSimulation(this.nodes)
      .force("link", d3.forceLink(this.links).id(d => d.id).distance(380).strength(0.5))
      .force("charge", d3.forceManyBody().strength(-5000))
      .force("center", d3.forceCenter(width / 2, height / 2))
      .force("x", d3.forceX(width / 2).strength(0.03))
      .force("y", d3.forceY(height / 2).strength(0.03))
      .force("collide", d3.forceCollide().radius(n => 60 + Math.min((this.degree[n.id] || 0) * 8, 80)).strength(1))
      .on("tick", () => this.ticked());
  }

  ticked() {
    this.nodes.forEach(n => {
       const g = this.nodeGroups[n.id];
       if (g) {
          g.setAttribute('transform', `translate(${n.x},${n.y}) scale(1)`);
       }
    });
    
    this.links.forEach(e => {
       if (e._el) {
          e._el.setAttribute('x1', e.source.x);
          e._el.setAttribute('y1', e.source.y);
          e._el.setAttribute('x2', e.target.x);
          e._el.setAttribute('y2', e.target.y);
          
          if (e._label) {
             const dx = e.target.x - e.source.x;
             const dy = e.target.y - e.source.y;
             const len = Math.hypot(dx, dy) || 1;
             // Only show label if the edge is long enough to fit text cleanly
             if (len < 80) {
               e._label.style.display = 'none';
             } else {
               e._label.style.display = '';
               // Perpendicular offset: shift the label 14px to the side of the line
               const px = -dy / len * 14;
               const py =  dx / len * 14;
               const mx = (e.source.x + e.target.x) / 2 + px;
               const my = (e.source.y + e.target.y) / 2 + py;
               e._label.setAttribute('x', mx);
               e._label.setAttribute('y', my);
             }
          }
       }
    });
  }

  dragstarted(event, d) {
    if (!event.active) this.simulation.alphaTarget(0.3).restart();
    d.fx = d.x;
    d.fy = d.y;
  }
  
  dragged(event, d) {
    d.fx = event.x;
    d.fy = event.y;
  }
  
  dragended(event, d) {
    if (!event.active) this.simulation.alphaTarget(0);
    // Keep d.fx / d.fy set — node stays pinned exactly where dropped.
    // To unpin a node the user can double-click it (see dblclick handler below).
  }

  buildGraph() {
    this.viewport.innerHTML = ''; // clear
    
    // Render Edges
    const SKIP_EDGE_TYPES = new Set(['MENTIONED_IN', 'MENTIONED_NEAR', 'EXTRACTED_FROM']);
    this.links.forEach(e => {
      // Skip structural provenance edges — they create a messy spider web without adding
      // investigative value. Investigators care about CALLED, HAS_PHONE, TRANSFERRED_TO etc.
      if (SKIP_EDGE_TYPES.has(e.type)) { e._el = null; e._label = null; return; }

      // D3 forceLink mutates e.source and e.target into node object references
      const a = typeof e.source === 'object' ? e.source : this.nodes.find(n => n.id === e.source);
      const b = typeof e.target === 'object' ? e.target : this.nodes.find(n => n.id === e.target);
      if (!a || !b) return;
      
      // Dotted = low-confidence/suggested (e.g. NLP-inferred, needs investigator confirmation)
      // Solid  = confirmed/deterministic (e.g. CDR row, financial transaction, FIR record)
      const isUncertain = (e.confidence != null && e.confidence < 0.6) ||
                          (typeof e.status === 'string' && e.status.includes('suggested'));
      const lineClass = 'edge ' + (isUncertain ? 'dotted' : 'solid');
      const line = this.el('line', {x1: a.x, y1: a.y, x2: b.x, y2: b.y, class: lineClass});
      
      // Solid edges: strong orange. Dotted edges: thin, muted, light to signal uncertainty
      if (isUncertain) {
        line.setAttribute('stroke', '#fdba74');       // pale orange
        line.setAttribute('stroke-width', '1');
        line.setAttribute('stroke-dasharray', '5 5');
        line.setAttribute('opacity', '0.5');
      } else {
        line.setAttribute('stroke', '#c2410c');       // strong dark orange
        line.setAttribute('stroke-width', '2');
        line.setAttribute('opacity', '0.9');
      }
      this.viewport.appendChild(line);
      e._el = line;
      
      const mx = (a.x + b.x) / 2, my = (a.y + b.y) / 2;
      
      // Suppress noisy high-frequency labels to reduce visual clutter
      const noisyTypes = new Set(['MENTIONED_IN', 'MENTIONED_NEAR', 'EXTRACTED_FROM']);
      const isCalling = (e.relationship_type === 'calling' || e.type === 'calling' || e.type === 'CALLED' || e.relationship_type === 'CALLED');
      const showLabel = !noisyTypes.has(e.type);
      
      const t = this.el('text', {
         x: mx, y: my - 6, 
         class: 'edge-label' + (isCalling ? ' calling-label' : ''), 
         'text-anchor': 'middle',
         'paint-order': 'stroke fill',
         'stroke': '#F8FAFC',
         'stroke-width': '4px',
         'stroke-linejoin': 'round'
      });
      t.textContent = isCalling ? 'calling' : (showLabel ? (e.type || 'LINK') : '');
      t.style.opacity = 0;
      t.style.fill = isCalling ? '#c2410c' : '#c2410c';
      t.style.fontWeight = '700';
      t.style.fontSize = '11px';
      t.style.letterSpacing = '0.5px';
      this.viewport.appendChild(t);
      e._label = t;
    });

    // Tooltip element container inside graph-wrap
    let tooltip = document.getElementById('graphTooltip');
    if (!tooltip) {
      tooltip = document.createElement('div');
      tooltip.id = 'graphTooltip';
      tooltip.className = 'graph-tooltip';
      const wrap = this.svg.closest('.graph-wrap') || this.svg.parentElement || document.body;
      wrap.appendChild(tooltip);
    }

    // Render Nodes
    const riskColors = {
      'red': '#EF4444',
      'orange': '#F97316',
      'yellow': '#EAB308',
      'none': '#0F766E'
    };
    
    this.nodes.forEach(n => {
      // Resolve phone for this specific node if available
      let nodePhone = n.phone || n.attributes?.phone || n.attributes?.phones?.[0];
      if (!nodePhone) {
        if (n.type === 'Phone' || n.type === 'PHONE') {
          nodePhone = n.name || n.value || n.id;
        } else if (n.type === 'Person' || n.type === 'PERSON') {
          // Look for adjacent phone node in links
          const phoneEdge = this.links.find(l => {
            const sid = typeof l.source === 'object' ? l.source.id : l.source;
            const tid = typeof l.target === 'object' ? l.target.id : l.target;
            return (sid === n.id || tid === n.id) && (l.type === 'HAS_PHONE' || l.type === 'USES');
          });
          if (phoneEdge) {
            const otherId = (typeof phoneEdge.source === 'object' ? phoneEdge.source.id : phoneEdge.source) === n.id
              ? (typeof phoneEdge.target === 'object' ? phoneEdge.target.id : phoneEdge.target)
              : (typeof phoneEdge.source === 'object' ? phoneEdge.source.id : phoneEdge.source);
            const otherNode = this.nodes.find(x => x.id === otherId);
            if (otherNode) nodePhone = otherNode.name || otherNode.value || otherNode.id;
          }
        }
      }
      n.phone = nodePhone;

      // Cap the max size so highly connected nodes don't overlap everything
      const r = 8 + Math.min((this.degree[n.id] || 0) * 1.5, 30);
      const isFlagged = n.flagged || n.status === 'REVIEW_REQUIRED' || n.risk_color === 'red';
      const statusClass = n.status === 'REVIEW_REQUIRED' ? ' REVIEW_REQUIRED' : '';
      const flagClass = isFlagged ? ' flagged' : '';
      const orphanClass = (this.degree[n.id] || 0) === 0 ? ' orphan' : '';
      const g = this.el('g', {class: 'node' + statusClass + flagClass + orphanClass, transform: `translate(${n.x},${n.y}) scale(0.4)`, 'data-id': n.id});
      g.style.opacity = 0;
      
      const strokeColor = riskColors[n.risk_color] || (isFlagged ? '#EF4444' : '#0F766E');
      const fillColor = strokeColor + '22'; // Colorful alpha fill
      
      if (isFlagged) {
         g.appendChild(this.el('circle', {
           class: 'ring red-flag-ring', 
           r: r + 7, 
           fill: 'none', 
           stroke: '#EF4444', 
           'stroke-width': '2.2',
           'stroke-dasharray': n.status === 'REVIEW_REQUIRED' ? '4 3' : 'none'
         }));
      }
      
      g.appendChild(this.el('circle', {class: 'body', r: r, fill: fillColor, stroke: strokeColor, 'stroke-width': 2}));
      
      // White background pill behind node name so edge lines don't obscure it
      const labelBg = this.el('rect', {
        rx: 4, ry: 4,
        fill: 'rgba(248,250,252,0.92)',
        x: -38, y: r + 4,
        width: 76, height: 14
      });
      const label = this.el('text', {y: r + 15, 'text-anchor': 'middle', 'font-size': '10', 'font-weight': '600', fill: '#1e293b'});
      label.textContent = (n.name || n.value || n.id || '').slice(0, 14);
      
      // Sub-label (type) with own background
      const subBg = this.el('rect', {
        rx: 3, ry: 3,
        fill: 'rgba(248,250,252,0.85)',
        x: -22, y: r + 18,
        width: 44, height: 12
      });
      const sub = this.el('text', {class: 'sub', y: r + 28, 'text-anchor': 'middle', 'font-size': '8.5', fill: '#64748b'});
      sub.textContent = n.type || '';
      
      g.appendChild(labelBg);
      g.appendChild(label);
      g.appendChild(subBg);
      g.appendChild(sub);
      
      // Mouseover / Pointerenter tooltip for node phone and details
      g.addEventListener('pointerenter', () => {
        const wrapEl = this.svg.closest('.graph-wrap') || this.svg.parentElement;
        if (!wrapEl) return;
        const wrapRect = wrapEl.getBoundingClientRect();
        const nodeRect = g.getBoundingClientRect();
        const left = nodeRect.left - wrapRect.left + nodeRect.width / 2;
        const top = nodeRect.top - wrapRect.top;

        const displayName = n.name || n.value || n.label || n.id;
        let tooltipContent = `
          <div class="tt-title">${displayName}</div>
          <div class="tt-type">${n.type || 'Entity'} &middot; ${this.degree[n.id] || 0} link(s)</div>
        `;
        if (n.phone) {
          tooltipContent += `<div class="tt-phone">📞 Phone: ${n.phone}</div>`;
        }
        if (isFlagged) {
          const reason = n.anomaly_reasons?.[0] || 'Flagged subnetwork — multiple evidence types';
          tooltipContent += `<div class="tt-flag">⚠️ ${reason}</div>`;
        }

        tooltip.innerHTML = tooltipContent;
        tooltip.style.left = `${left}px`;
        tooltip.style.top = `${top}px`;
        tooltip.classList.add('visible');
      });

      g.addEventListener('pointerleave', () => {
        tooltip.classList.remove('visible');
      });

      g.addEventListener('pointerdown', (ev) => { ev.stopPropagation(); });
      g.addEventListener('click', (ev) => { 
        ev.stopPropagation(); 
        tooltip.classList.remove('visible');
        if(this.onSelectNode) this.onSelectNode(n); 
        this.selectNodeUI(n.id);
      });
      // Double-click releases the pin so node flows freely again
      g.addEventListener('dblclick', (ev) => {
        ev.stopPropagation();
        n.fx = null;
        n.fy = null;
        this.simulation.alphaTarget(0.1).restart();
        setTimeout(() => this.simulation.alphaTarget(0), 500);
      });
      
      // Add D3 drag behavior
      d3.select(g).call(d3.drag()
        .on("start", (event) => {
          tooltip.classList.remove('visible');
          this.dragstarted(event, n);
        })
        .on("drag", (event) => {
          tooltip.classList.remove('visible');
          this.dragged(event, n);
        })
        .on("end", (event) => this.dragended(event, n))
      );
      
      this.viewport.appendChild(g);
      this.nodeGroups[n.id] = g;
    });
  }

  selectNodeUI(id) {
     Object.values(this.nodeGroups).forEach(g => g.classList.remove('selected'));
     if(this.nodeGroups[id]) {
         this.nodeGroups[id].classList.add('selected');
     }
  }

  revealGraph() {
    let i = 0;
    this.nodes.forEach(n => {
      const g = this.nodeGroups[n.id];
      setTimeout(() => {
        g.style.transition = reduced ? 'opacity 200ms ease' : 'opacity 280ms ease'; // Removed transform transition to prevent fighting with D3
        g.style.opacity = 1;
        g.setAttribute('transform', `translate(${n.x},${n.y}) scale(1)`);
      }, i * 10);
      i++;
    });
    
    this.links.forEach((e, idx) => {
      setTimeout(() => {
        // Just fade in labels — no dashoffset animation needed anymore
        e._label.style.transition = 'opacity 300ms ease';
        e._label.style.opacity = 1;
      }, 260 + idx * 70);
    });
    setTimeout(() => { 
        this.fitGraphToScreen();
        const hint = document.getElementById('graphHint');
        if(hint) hint.classList.add('show'); 
    }, 900);
  }

  fitGraphToScreen() {
    if(this.nodes.length === 0) return;
    let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
    this.nodes.forEach(n => {
      if(n.x < minX) minX = n.x;
      if(n.x > maxX) maxX = n.x;
      if(n.y < minY) minY = n.y;
      if(n.y > maxY) maxY = n.y;
    });
    
    const padding = 120;
    const width = maxX - minX + padding * 2;
    const height = maxY - minY + padding * 2;
    
    const scaleX = 880 / (width || 1);
    const scaleY = 520 / (height || 1);
    const targetZoom = Math.min(scaleX, scaleY, 1.2); 
    
    const cx = (minX + maxX) / 2;
    const cy = (minY + maxY) / 2;
    
    const targetPanX = 880/2 - cx * targetZoom;
    const targetPanY = 520/2 - cy * targetZoom;
    
    this.panSpringX.set(targetPanX);
    this.panSpringY.set(targetPanY);
    this.zoomSpring.set(targetZoom);
  }

  /* ----- Pan & Zoom Logic ----- */
  initPanning() {
    this.panX = 0; this.panY = 0; this.zoom = 1;
    let dragging = false, startX = 0, startY = 0, baseX = 0, baseY = 0;
    let history = [];
    
    this.applyTransform = () => { 
        this.viewport.setAttribute('transform', `translate(${this.panX},${this.panY}) scale(${this.zoom})`); 
    };
    
    this.panSpringX = new Spring(0, {damping: 1, response: 0.5, onUpdate: v => { this.panX = v; this.applyTransform(); }});
    this.panSpringY = new Spring(0, {damping: 1, response: 0.5, onUpdate: v => { this.panY = v; this.applyTransform(); }});
    this.zoomSpring = new Spring(1, {damping: 1, response: 0.5, onUpdate: v => { this.zoom = v; this.applyTransform(); }});
    
    this.svg.addEventListener('wheel', (ev) => {
      ev.preventDefault();
      let z = this.zoomSpring.target;
      const zoomFactor = Math.exp(ev.deltaY * -0.002);
      z *= zoomFactor;
      z = Math.max(0.1, Math.min(z, 4)); 
      
      const rect = this.svg.getBoundingClientRect();
      const scale = 880 / rect.width;
      const mx = (ev.clientX - rect.left) * scale;
      const my = (ev.clientY - rect.top) * scale;
      
      const newPanX = mx - (mx - this.panSpringX.target) * (z / this.zoomSpring.target);
      const newPanY = my - (my - this.panSpringY.target) * (z / this.zoomSpring.target);
      
      this.panSpringX.set(newPanX);
      this.panSpringY.set(newPanY);
      this.zoomSpring.set(z);
    });

    this.svg.addEventListener('pointerdown', (ev) => {
      dragging = true; this.svg.classList.add('grabbing');
      this.svg.setPointerCapture(ev.pointerId);
      startX = ev.clientX; startY = ev.clientY; baseX = this.panX; baseY = this.panY;
      history = [{x: ev.clientX, y: ev.clientY, t: performance.now()}];
    });
    
    this.svg.addEventListener('pointermove', (ev) => {
      if (!dragging) return;
      const scale = 880 / this.svg.getBoundingClientRect().width;
      const dx = (ev.clientX - startX) * scale, dy = (ev.clientY - startY) * scale;
      this.panX = baseX + dx;
      this.panY = baseY + dy;
      this.applyTransform();
      history.push({x: ev.clientX, y: ev.clientY, t: performance.now()});
      if (history.length > 5) history.shift();
    });
    
    const endDrag = (ev) => {
      if (!dragging) return;
      dragging = false; this.svg.classList.remove('grabbing');
      let vx = 0, vy = 0;
      if (history.length >= 2) {
        const a = history[0], b = history[history.length - 1];
        const dt = (b.t - a.t) || 16;
        const scale = 880 / this.svg.getBoundingClientRect().width;
        vx = (b.x - a.x) * scale / dt * 16; vy = (b.y - a.y) * scale / dt * 16;
      }
      this.panSpringX.value = this.panX; this.panSpringX.set(this.panX + vx * 4, vx * 8);
      this.panSpringY.value = this.panY; this.panSpringY.set(this.panY + vy * 4, vy * 8);
    };
    
    this.svg.addEventListener('pointerup', endDrag);
    this.svg.addEventListener('pointercancel', endDrag);
  }
}
