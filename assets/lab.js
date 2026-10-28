/* Exact finite Jordan-chain explorer; local DOM operations only. */
(() => {
  'use strict';
  const input = document.getElementById('block-sizes');
  if (!input) return;
  const status = document.getElementById('chain-status');
  const diagram = document.getElementById('chain-diagram');
  const host = document.getElementById('chain-table');
  const render = () => {
    const raw = input.value.trim();
    const sizes = raw.split(',').map(s => Number(s.trim()));
    if (!/^\s*\d+(\s*,\s*\d+)*\s*$/.test(raw) ||
        sizes.some(s => !Number.isInteger(s) || s < 1 || s > 8) ||
        sizes.reduce((a, b) => a + b, 0) > 32) {
      status.textContent = 'Use comma-separated integers from 1 to 8, with total at most32.';
      diagram.replaceChildren(); host.replaceChildren(); return;
    }
    const total = sizes.reduce((a, b) => a + b, 0);
    const largest = Math.max(...sizes);
    status.textContent = `${sizes.length} blocks; dimension ${total}; largest block ${largest}.`;
    diagram.replaceChildren();
    sizes.forEach((size, i) => {
      const row = document.createElement('p'); row.className = 'chain-row';
      row.textContent = `Chain ${i + 1}: 0 ← ` +
        Array.from({length: size}, (_, j) => `u${i + 1},${j + 1}`).join(' ← ');
      diagram.append(row);
    });
    const table = document.createElement('table');
    const caption = document.createElement('caption'); caption.textContent = 'Kernel growth for this eigenvalue'; table.append(caption);
    const head = document.createElement('thead'); const hr = document.createElement('tr');
    for (const label of ['Power k', 'Kernel dimension dₖ', 'Blocks of size at least k']) {
      const th = document.createElement('th'); th.textContent = label; th.scope = 'col'; hr.append(th);
    }
    head.append(hr); table.append(head);
    const body = document.createElement('tbody');
    for (let k = 0; k <= largest + 1; k++) {
      const row = document.createElement('tr');
      const values = [k, sizes.reduce((sum, s) => sum + Math.min(k, s), 0),
        k === 0 ? '—' : sizes.filter(s => s >= k).length];
      for (const value of values) { const td = document.createElement('td'); td.textContent = String(value); row.append(td); }
      body.append(row);
    }
    table.append(body); const wrap = document.createElement('div'); wrap.className = 'table-wrap'; wrap.append(table); host.replaceChildren(wrap);
  };
  document.getElementById('explore-chains').addEventListener('click', render);
  input.addEventListener('keydown', e => { if (e.key === 'Enter') render(); });
  render();
})();
