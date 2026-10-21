// Zoom for the details page only: wheel or pinch zooms at the pointer, drag moves, double-tap resets.
// No library, no request. The picture page has no script.
document.querySelectorAll('svg.chart').forEach(function (svg) {
  var vb = svg.viewBox.baseVal, base = {x: vb.x, y: vb.y, w: vb.width, h: vb.height}, ptrs = {}, dist = null;
  function at(cx, cy) {
    var r = svg.getBoundingClientRect();
    return {x: vb.x + (cx - r.left) / r.width * vb.width, y: vb.y + (cy - r.top) / r.height * vb.height};
  }
  function clamp() {
    vb.x = Math.min(Math.max(vb.x, base.x), base.x + base.w - vb.width);
    vb.y = Math.min(Math.max(vb.y, base.y), base.y + base.h - vb.height);
  }
  function zoom(factor, c) {
    var w = Math.min(base.w, Math.max(base.w / 6, vb.width * factor)), h = w * base.h / base.w;
    vb.x = c.x - (c.x - vb.x) * w / vb.width; vb.y = c.y - (c.y - vb.y) * h / vb.height;
    vb.width = w; vb.height = h; clamp();
  }
  svg.addEventListener('wheel', function (e) {
    e.preventDefault(); zoom(Math.exp(e.deltaY * 0.0015), at(e.clientX, e.clientY));
  }, {passive: false});
  svg.addEventListener('pointerdown', function (e) {
    svg.setPointerCapture(e.pointerId); ptrs[e.pointerId] = {x: e.clientX, y: e.clientY};
  });
  svg.addEventListener('pointermove', function (e) {
    var last = ptrs[e.pointerId]; if (!last) { return; }
    ptrs[e.pointerId] = {x: e.clientX, y: e.clientY};
    var ids = Object.keys(ptrs), r = svg.getBoundingClientRect();
    if (ids.length === 1) {
      vb.x -= (e.clientX - last.x) / r.width * vb.width; vb.y -= (e.clientY - last.y) / r.height * vb.height; clamp();
    } else if (ids.length === 2) {
      var a = ptrs[ids[0]], b = ptrs[ids[1]], d = Math.hypot(a.x - b.x, a.y - b.y);
      if (dist) { zoom(dist / d, at((a.x + b.x) / 2, (a.y + b.y) / 2)); }
      dist = d;
    }
  });
  function up(e) { delete ptrs[e.pointerId]; if (Object.keys(ptrs).length < 2) { dist = null; } }
  svg.addEventListener('pointerup', up); svg.addEventListener('pointercancel', up);
  svg.addEventListener('dblclick', function () { vb.x = base.x; vb.y = base.y; vb.width = base.w; vb.height = base.h; });
});
