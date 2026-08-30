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
    const cx = 440; // Center X of 880 width SVG
    const cy = 260; // Center Y of 520 height SVG
    const radius = 180;
    
    const n = this.nodes.length;
    this.nodes.forEach((node, i) => {
      const angle = (i / n) * 2 * Math.PI;
      node.x = cx + radius * Math.cos(angle);
      node.y = cy + radius * Math.sin(angle);
    });
  }

  buildGraph() {
    this.viewport.innerHTML = ''; // clear
    
    // Render Edges
    this.links.forEach(e => {
      const a = this.nodes.find(n => n.id === e.source);
      const b = this.nodes.find(n => n.id === e.target);
      if (!a || !b) return;
      
      const lineClass = 'edge ' + (e.line_type === 'dotted' ? 'dotted' : 'solid');
      const line = this.el('line', {x1: a.x, y1: a.y, x2: b.x, y2: b.y, class: lineClass});
      
      const len = Math.hypot(b.x - a.x, b.y - a.y);
      line.style.strokeDasharray = e.line_type === 'dotted' ? '4 4' : len;
      if (e.line_type !== 'dotted') {
         line.style.strokeDashoffset = len;
      }
      this.viewport.appendChild(line);
      e._el = line;
      
      const mx = (a.x + b.x) / 2, my = (a.y + b.y) / 2;
      const t = this.el('text', {x: mx, y: my - 4, class: 'edge-label', 'text-anchor': 'middle'});
      t.textContent = e.confidence ? (e.confidence * 100).toFixed(0) + '%' : 'LINK';
      t.style.opacity = 0;
      this.viewport.appendChild(t);
      e._label = t;
    });

    // Render Nodes
    const riskColors = {
      'red': '#EF4444',
      'orange': '#F97316',
      'yellow': '#EAB308',
      'none': '#0F766E'
    };
    
    this.nodes.forEach(n => {
      const r = 14 + (this.degree[n.id] || 0) * 3;
      const statusClass = n.status === 'REVIEW_REQUIRED' ? ' REVIEW_REQUIRED' : '';
      const g = this.el('g', {class: 'node' + statusClass, transform: `translate(${n.x},${n.y}) scale(0.4)`, 'data-id': n.id});
      g.style.opacity = 0;
      
      const strokeColor = riskColors[n.risk_color] || '#0F766E';
      const fillColor = strokeColor + '22'; // add alpha
      
      if (n.status === 'REVIEW_REQUIRED') {
         g.appendChild(this.el('circle', {class: 'ring', r: r + 8, fill: 'none', stroke: strokeColor, 'stroke-width': 1.4}));
      }
      
      g.appendChild(this.el('circle', {class: 'body', r: r, fill: fillColor, stroke: strokeColor}));
      
      const label = this.el('text', {y: r + 15, 'text-anchor': 'middle'});
      label.textContent = n.name || n.id;
      
      const sub = this.el('text', {class: 'sub', y: r + 27, 'text-anchor': 'middle'});
      sub.textContent = n.historical_firs > 0 ? `${n.historical_firs} FIRs` : 'Clean';
      
      g.appendChild(label);
      g.appendChild(sub);
      
      g.addEventListener('pointerdown', (ev) => { ev.stopPropagation(); });
      g.addEventListener('click', (ev) => { 
        ev.stopPropagation(); 
        if(this.onSelectNode) this.onSelectNode(n); 
        this.selectNodeUI(n.id);
      });
      
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
        g.style.transition = reduced ? 'opacity 200ms ease' : 'opacity 280ms ease, transform 480ms cubic-bezier(.2,.9,.3,1)';
        g.style.opacity = 1;
        g.setAttribute('transform', `translate(${n.x},${n.y}) scale(1)`);
      }, i * 80);
      i++;
    });
    
    this.links.forEach((e, idx) => {
      setTimeout(() => {
        if (e.line_type !== 'dotted') {
            e._el.style.transition = 'stroke-dashoffset 420ms ease-out';
            e._el.style.strokeDashoffset = 0;
        }
        e._label.style.transition = 'opacity 300ms ease';
        e._label.style.opacity = 1;
      }, 260 + idx * 70);
    });
    setTimeout(() => { 
        const hint = document.getElementById('graphHint');
        if(hint) hint.classList.add('show'); 
    }, 900);
  }

  /* ----- Pan Logic ----- */
  initPanning() {
    let panX = 0, panY = 0, dragging = false, startX = 0, startY = 0, baseX = 0, baseY = 0;
    let history = [];
    const bounds = {minX: -400, maxX: 400, minY: -400, maxY: 400};
    
    const applyPan = () => { this.viewport.setAttribute('transform', `translate(${panX},${panY})`); };
    const panSpringX = new Spring(0, {damping: 1, response: 0.5, onUpdate: v => { panX = v; applyPan(); }});
    const panSpringY = new Spring(0, {damping: 1, response: 0.5, onUpdate: v => { panY = v; applyPan(); }});
    
    const clampRubber = (v, lo, hi) => {
      if (v < lo) return lo - (lo - v) * 0.35;
      if (v > hi) return hi + (v - hi) * 0.35;
      return v;
    };
    
    this.svg.addEventListener('pointerdown', (ev) => {
      dragging = true; this.svg.classList.add('grabbing');
      this.svg.setPointerCapture(ev.pointerId);
      startX = ev.clientX; startY = ev.clientY; baseX = panX; baseY = panY;
      history = [{x: ev.clientX, y: ev.clientY, t: performance.now()}];
    });
    
    this.svg.addEventListener('pointermove', (ev) => {
      if (!dragging) return;
      const scale = 880 / this.svg.getBoundingClientRect().width;
      const dx = (ev.clientX - startX) * scale, dy = (ev.clientY - startY) * scale;
      panX = clampRubber(baseX + dx, bounds.minX, bounds.maxX);
      panY = clampRubber(baseY + dy, bounds.minY, bounds.maxY);
      applyPan();
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
      const targetX = Math.min(Math.max(panX + vx * 4, bounds.minX), bounds.maxX);
      const targetY = Math.min(Math.max(panY + vy * 4, bounds.minY), bounds.maxY);
      panSpringX.value = panX; panSpringX.set(targetX, vx * 8);
      panSpringY.value = panY; panSpringY.set(targetY, vy * 8);
    };
    
    this.svg.addEventListener('pointerup', endDrag);
    this.svg.addEventListener('pointercancel', endDrag);
  }
}
