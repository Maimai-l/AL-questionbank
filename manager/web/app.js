/* 题库数据管理 (docs/data-manager.md). React without a build step: h = createElement.
   Pages: #/query, #/sets/<id>[/paper | /export/<template>], #/templates/<id>, #/templates/flows, #/flows/<id>, #/settings. */
(function () {
  'use strict';
  const { useState, useEffect, useMemo, useRef, useCallback } = React;
  const h = React.createElement;
  const E = window.Endfield;

  // ------------------------------------------------------------------ helpers

  const api = (url, opts) => fetch(url, opts).then((r) => {
    if (!r.ok) return r.text().then((t) => { throw new Error(t || r.statusText); });
    return r.json();
  });
  const send = (method, url, body) => api(url, {
    method, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body),
  });
  const MONTH = { 3: '3 月', 6: '6 月', 11: '11 月' };
  const sum = (rows) => rows.reduce((a, r) => a + (r.marks || 0), 0);

  // Dropdown menus (the design system's .dd .menu) sit in the scrolling panels, which
  // clip them. An open menu is taken out of the flow (position: fixed), as wide as its
  // field, below it or above it when there is more room there, and kept on screen.
  function placeMenu(menu) {
    const field = menu.parentElement.querySelector('.select, .ibtn, button') || menu.parentElement;
    const r = field.getBoundingClientRect();
    if (!r.width) return;
    const s = menu.style;
    Object.assign(s, { position: 'fixed', right: 'auto', bottom: 'auto', left: '0px', top: '0px',
      minWidth: r.width + 'px', width: 'max-content', maxWidth: Math.max(r.width, 360) + 'px' });
    const below = innerHeight - r.bottom - 12, above = r.top - 12;
    const up = menu.scrollHeight > below && above > below;
    s.maxHeight = Math.min(320, up ? above : below) + 'px';
    const m = menu.getBoundingClientRect();   // a transformed ancestor (a dialog) moves the origin
    const toRight = menu.parentElement.classList.contains('more-dd');   // a "more" menu opens toward the page, under its button
    const left = Math.max(8, Math.min(toRight ? r.right - m.width : r.left, innerWidth - m.width - 8));
    const top = up ? r.top - 4 - m.height : r.bottom + 4;
    s.left = left - m.left + 'px';
    s.top = top - m.top + 'px';
  }
  const openMenus = () => document.querySelectorAll('.dd > .menu:not([hidden])');
  new MutationObserver((list) => list.forEach((x) => {
    if (x.target.matches('.dd > .menu:not([hidden])')) placeMenu(x.target);
  })).observe(document.documentElement, { subtree: true, attributes: true, attributeFilter: ['hidden'] });
  addEventListener('scroll', () => openMenus().forEach(placeMenu), true);
  addEventListener('resize', () => openMenus().forEach(placeMenu));

  function useHash() {
    const [hash, setHash] = useState(location.hash || '#/query');
    useEffect(() => {
      const on = () => setHash(location.hash || '#/query');
      addEventListener('hashchange', on);
      return () => removeEventListener('hashchange', on);
    }, []);
    return hash;
  }

  /** Text with $...$ and $$...$$ rendered by KaTeX. */
  function Tex({ text, className, tag }) {
    const ref = useRef(null);
    useEffect(() => {
      const el = ref.current;
      if (!el) return;
      el.textContent = text || '';
      const go = () => window.renderMathInElement && window.renderMathInElement(el, {
        delimiters: [{ left: '$$', right: '$$', display: true }, { left: '$', right: '$', display: false }],
        throwOnError: false,
      });
      if (window.renderMathInElement) go(); else addEventListener('load', go, { once: true });
    }, [text]);
    return h(tag || 'span', { ref, className });
  }

  /** Markdown as the admissions solutions use it: paragraphs and **bold**. */
  function Markdown({ text }) {
    const paras = (text || '').split(/\n{2,}/).filter((p) => p.trim());
    return h('div', { className: 'dm-prose' }, paras.map((p, i) => {
      const bits = p.split(/\*\*(.+?)\*\*/g);
      return h('p', { key: i }, bits.map((b, j) => (j % 2 ? h('b', { key: j }, b) : h(Tex, { key: j, text: b }))));
    }));
  }

  /** "s23 12 q5", "9709/12/M/J/23 Q5", "m24 12" as a filter on the rows; null if not a code. */
  function parseCode(q) {
    const s = q.toLowerCase().replace(/\s+/g, ' ').trim();
    let m = s.match(/^([msw])\s?(\d{2})\s+(\d{2})(?:\s+q?(\d{1,2}))?$/);
    if (m) return { season: { m: 3, s: 6, w: 11 }[m[1]], yy: +m[2], paper: m[3], q: m[4] ? +m[4] : null };
    m = s.match(/^\d{4}\/(\d{2})\/(f\/m|m\/j|o\/n)\/(\d{2})(?:\s+q?(\d{1,2}))?$/);
    if (m) return { season: { 'f/m': 3, 'm/j': 6, 'o/n': 11 }[m[2]], yy: +m[3], paper: m[1], q: m[4] ? +m[4] : null };
    return null;
  }

  // A pencil, drawn like the design system's line icons (its sprite has none).
  const sprite = document.getElementById('ef-sprite');
  if (sprite && !document.getElementById('i-edit')) {
    sprite.insertAdjacentHTML('beforeend', '<symbol id="i-edit" viewBox="0 0 16 16"><path d="M10.6 2.4l3 3L5.4 13.6H2.4v-3zM8.9 4.1l3 3"/></symbol>');
  }

  // ------------------------------------------------------------------ actions

  /** A borderless icon button with its name as a tooltip: the page's actions. */
  const act = (icon, label, onClick, more) => h(E.IconButton, { icon, label, variant: 'ghost', size: 'sm', tooltip: 'below', onClick, ...more });

  /** Actions that are seldom used or destructive, behind a "more" button. Uses the
      design system's dropdown menu (.dd .menu), placed by placeMenu. */
  function MoreMenu({ label = '更多', items }) {
    const [open, setOpen] = useState(false);
    const ref = useRef(null);
    useEffect(() => {
      if (!open) return undefined;
      const away = (e) => { if (ref.current && !ref.current.contains(e.target)) setOpen(false); };
      const key = (e) => { if (e.key === 'Escape') setOpen(false); };
      document.addEventListener('pointerdown', away);
      document.addEventListener('keydown', key);
      return () => { document.removeEventListener('pointerdown', away); document.removeEventListener('keydown', key); };
    }, [open]);
    return h('div', { ref, className: 'dd more-dd' },
      h(E.IconButton, { icon: 'i-more', label, variant: 'ghost', size: 'sm', tooltip: open ? undefined : 'below',
        'aria-haspopup': 'menu', 'aria-expanded': open, onClick: () => setOpen(!open) }),
      h('div', { className: 'menu', role: 'menu', hidden: !open },
        items.filter(Boolean).map((it) => h('button', { key: it.label, type: 'button', role: 'menuitem',
          className: 'menu-item' + (it.danger ? ' is-danger' : ''), onClick: () => { setOpen(false); it.onClick(); } }, it.label))));
  }

  /** Page actions rendered into the top bar's action slot (App's acts element). */
  const TopActs = ({ el, children }) => (el ? ReactDOM.createPortal(children, el) : null);

  // ------------------------------------------------------------------ table

  const SORT_MARK = h('svg', { viewBox: '0 0 12 12', 'aria-hidden': 'true' }, h('path', { d: 'M2 4 H10 L6 10 Z', fill: 'currentColor' }));

  /** The design system's table (same markup and styles) with the usual selection:
      click selects the row, Cmd/Ctrl-click adds or removes it, Shift-click selects the
      range from the last clicked row, and dragging over rows selects them. On a touch
      screen a tap adds or removes the row. Arrow keys move, Shift+arrow extends,
      Space toggles, Cmd/Ctrl+A selects all, Escape clears. onActivate(key) gets the
      row that was clicked last (the query page shows it in the detail panel). */
  function SelTable({ columns, rows, rowKey = 'id', selected, onSelectedChange, onActivate, minWidth, ariaLabel }) {
    const [sort, setSort] = useState(null);
    const anchor = useRef(null);
    const drag = useRef(null);
    const body = useRef(null);
    const key = (r) => String(r[rowKey]);
    const value = (c, r) => (c.sortValue ? c.sortValue(r) : r[c.key]);
    const view = useMemo(() => {
      const c = sort && columns.find((x) => x.key === sort.key);
      if (!c) return rows;
      const d = sort.dir === 'ascending' ? 1 : -1;
      return rows.slice().sort((a, b) => {
        const x = value(c, a), y = value(c, b);
        return (typeof x === 'number' && typeof y === 'number' ? x - y : String(x).localeCompare(String(y), 'zh-Hans-CN')) * d
          || key(a).localeCompare(key(b));
      });
    }, [rows, sort, columns]);
    const keys = useMemo(() => view.map(key), [view]);
    const set = (ks) => onSelectedChange([...new Set(ks)]);
    const range = (a, b) => {
      const i = keys.indexOf(a), j = keys.indexOf(b);
      return i < 0 || j < 0 ? [b] : keys.slice(Math.min(i, j), Math.max(i, j) + 1);
    };
    const all = keys.length > 0 && keys.every((k) => selected.includes(k));

    useEffect(() => {
      const up = () => { drag.current = null; };
      addEventListener('pointerup', up);
      addEventListener('pointercancel', up);
      return () => { removeEventListener('pointerup', up); removeEventListener('pointercancel', up); };
    }, []);

    const down = (e, k) => {
      if (e.button !== 0 || e.target.closest('button,a,input,label,select,textarea')) return;
      const mods = e.metaKey || e.ctrlKey;
      if (e.pointerType !== 'mouse') {                 // touch and pen: a tap toggles
        set(selected.includes(k) ? selected.filter((x) => x !== k) : selected.concat(k));
      } else if (e.shiftKey && anchor.current) {
        e.preventDefault();                            // no text selection
        set((mods ? selected : []).concat(range(anchor.current, k)));
        onActivate && onActivate(k);
        return;
      } else if (mods) {
        const on = !selected.includes(k);
        const base = on ? selected.concat(k) : selected.filter((x) => x !== k);
        set(base);
        drag.current = { from: k, base: on ? selected : base, on };
      } else {
        set([k]);
        drag.current = { from: k, base: [], on: true };
      }
      if (e.pointerType === 'mouse') { e.preventDefault(); e.currentTarget.focus(); }
      anchor.current = k;
      onActivate && onActivate(k);
    };
    const over = (k) => {
      const d = drag.current;
      if (!d) return;
      const span = range(d.from, k);
      set(d.on ? d.base.concat(span) : d.base.filter((x) => !span.includes(x)));
    };
    const keyDown = (e, k) => {
      if (e.target !== e.currentTarget) return;
      if (e.key === ' ') {
        e.preventDefault();
        set(selected.includes(k) ? selected.filter((x) => x !== k) : selected.concat(k));
        anchor.current = k; onActivate && onActivate(k);
      } else if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
        e.preventDefault();
        const next = keys[keys.indexOf(k) + (e.key === 'ArrowDown' ? 1 : -1)];
        if (!next) return;
        if (e.shiftKey) set(range(anchor.current || k, next));
        else { set([next]); anchor.current = next; }
        onActivate && onActivate(next);
        const tr = body.current.querySelector(`tr[data-k="${CSS.escape(next)}"]`);
        tr && tr.focus();
      } else if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'a') {
        e.preventDefault(); set(keys);
      } else if (e.key === 'Escape') set([]);
    };

    const head = (c, i) => {
      const num = c.kind === 'number', on = sort && sort.key === c.key;
      const box = i === 0 ? h('button', { className: 'tbl-all', type: 'button', role: 'checkbox', 'aria-checked': all,
        'aria-label': '全选', onClick: () => set(all ? [] : keys) }) : null;
      if (c.sortable === false) return h('th', { key: c.key, scope: 'col', className: num ? 'num' : undefined }, box, c.label);
      const next = () => setSort({ key: c.key, dir: on ? (sort.dir === 'descending' ? 'ascending' : 'descending') : num ? 'descending' : 'ascending' });
      return h('th', { key: c.key, scope: 'col', className: num ? 'num' : undefined, 'aria-sort': on ? sort.dir : undefined }, box,
        h('button', { type: 'button', onClick: next },
          h('span', { className: 'in' }, num ? [SORT_MARK, h('span', { key: 'l' }, c.label)] : [h('span', { key: 'l' }, c.label), SORT_MARK])));
    };
    const cell = (c, r) => {
      const v = r[c.key];
      if (c.kind === 'number') return h('td', { key: c.key, className: 'num' }, h('b', null, typeof v === 'number' ? v.toLocaleString('en-US') : v), c.unit);
      return h('td', { key: c.key, className: c.kind === 'id' ? 'c-id' : undefined }, v);
    };
    return h('div', { className: 'tbl-frame' }, h('i'), h('i'), h('i'), h('i'),
      h('div', { className: 'tbl-scroll' },
        h('table', { className: 'tbl sel-tbl', 'aria-multiselectable': true, 'aria-label': ariaLabel, style: minWidth ? { minWidth } : undefined },
          h('colgroup', null, columns.map((c) => h('col', { key: c.key, style: c.width ? { width: c.width } : undefined }))),
          h('thead', null, h('tr', null, columns.map(head))),
          h('tbody', { ref: body }, view.map((r) => {
            const k = key(r);
            return h('tr', { key: k, 'data-k': k, tabIndex: 0, 'aria-selected': selected.includes(k),
              onPointerDown: (e) => down(e, k), onPointerEnter: () => over(k), onKeyDown: (e) => keyDown(e, k) },
            columns.map((c) => cell(c, r)));
          })))));
  }

  // ------------------------------------------------------------------ name rule (docs 7.5)

  function queryName(meta, f) {
    const comps = meta.components.filter((c) => f.components.has(c.value)).map((c) => c.label);
    const topics = meta.topics.filter((t) => f.topics.has(t.value) && f.components.has(t.component));
    const allTopics = meta.topics.filter((t) => f.components.has(t.component));
    const topicPart = topics.length && topics.length < allTopics.length
      ? topics.map((t) => t.label.replace(/^\S+\s/, '')).join('、') : '';
    const years = f.from === f.to ? String(f.from) : `${f.from}-${f.to}`;
    return [meta.exam, comps.join('、'), topicPart, years].filter(Boolean).join(' ');
  }

  function wholePaper(rows, allRows) {
    if (!rows.length) return null;
    const code = rows[0].code;
    if (!rows.every((r) => r.code === code)) return null;
    return allRows.filter((r) => r.code === code).length === rows.length ? code : null;
  }

  // ------------------------------------------------------------------ query page

  function Facet({ title, items, picked, onChange, grid }) {
    const all = items.length > 0 && items.every((i) => picked.has(i.value));
    const some = items.some((i) => picked.has(i.value));
    const toggle = (v) => {
      const next = new Set(picked);
      next.has(v) ? next.delete(v) : next.add(v);
      onChange(next);
    };
    return h('section', null,
      h('div', { className: 'fx-head' },
        h(E.Checkbox, {
          checked: all, indeterminate: some && !all,
          onChange: () => onChange(all ? new Set() : new Set(items.map((i) => i.value))),
        }, title),
        h('span', { className: 'fx-n' }, `${items.filter((i) => picked.has(i.value)).length} / ${items.length}`)),
      h('div', { className: grid ? 'fx-grid' : null }, items.map((i) => h('div', { className: 'fx-row', key: i.value },
        h(E.Checkbox, { checked: picked.has(i.value), onChange: () => toggle(i.value) }, i.label),
        h('span', { className: 'fx-n' }, i.n)))));
  }

  function defaults(meta) {
    const first = meta.components[0] ? meta.components[0].value : null;
    return {
      components: new Set(first ? [first] : []),
      topics: new Set(meta.topics.filter((t) => t.component === first).map((t) => t.value)),
      tasks: null,                           // null: all
      from: meta.years[0], to: meta.years[meta.years.length - 1],
    };
  }

  function QueryPage({ metas, search, clearSearch, sets, reloadSets, toast }) {
    const [exam, setExam] = useState('9709');
    const meta = metas.find((m) => m.exam === exam);
    const [rowsByExam, setRowsByExam] = useState({});
    const [f, setF] = useState(() => defaults(meta));
    const [hits, setHits] = useState(null);
    const [selected, setSelected] = useState([]);
    const [focus, setFocus] = useState(null);
    const [adding, setAdding] = useState(false);
    const allRows = rowsByExam[exam] || [];

    useEffect(() => {
      if (!rowsByExam[exam]) api('/api/questions?exam=' + exam).then((r) => setRowsByExam((o) => ({ ...o, [exam]: r })));
    }, [exam]);
    useEffect(() => {
      if (!search) { setHits(null); return; }
      const code = parseCode(search);
      if (code) { setHits({ code }); return; }
      let live = true;
      api(`/api/search?exam=${exam}&q=${encodeURIComponent(search)}`).then((ids) => { if (live) setHits({ ids: new Set(ids) }); });
      return () => { live = false; };
    }, [search, exam]);

    const changeExam = (v) => {
      setExam(v); setF(defaults(metas.find((m) => m.exam === v))); setSelected([]); setFocus(null);
    };
    const setComponents = (next) => {
      const topics = new Set(meta.topics.filter((t) => next.has(t.component)).map((t) => t.value));
      setF({ ...f, components: next, topics });
    };

    // the task types on offer come from the papers and years picked; the count beside each
    // follows the search and the topics too, like the counts beside the topics
    const taskItems = useMemo(() => {
      const all = {}, n = {};
      allRows.forEach((r) => {
        if (!f.components.has(r.component) || r.year < f.from || r.year > f.to) return;
        const counted = (!hits || !hits.ids || hits.ids.has(r.id)) && (!r.topic || f.topics.has(r.topic));
        r.tasks.forEach((t) => { all[t] = (all[t] || 0) + 1; if (counted) n[t] = (n[t] || 0) + 1; });
      });
      return Object.keys(all).sort((a, b) => all[b] - all[a]).map((t) => ({
        value: t, label: t.replace(/_/g, ' ').replace(/^./, (c) => c.toUpperCase()), n: n[t] || 0,
      }));
    }, [allRows, f.components, f.topics, f.from, f.to, hits]);
    const tasks = f.tasks || new Set(taskItems.map((t) => t.value));

    // A paper code (s23 12 q5, 9709/12/M/J/23) finds that paper or question whatever the
    // conditions on the left; words narrow the questions the conditions select.
    const isHit = (r) => {
      if (!hits) return true;
      if (hits.ids) return hits.ids.has(r.id);
      const c = hits.code;
      return r.month === c.season && r.year % 100 === c.yy && r.paper === c.paper && (!c.q || r.q === c.q);
    };
    const rows = useMemo(() => allRows.filter((r) => {
      if (hits && hits.code) return isHit(r);
      if (!isHit(r)) return false;
      if (!f.components.has(r.component) || r.year < f.from || r.year > f.to) return false;
      if (r.topic && !f.topics.has(r.topic)) return false;
      if (taskItems.length && r.tasks.length && !r.tasks.some((t) => tasks.has(t))) return false;
      return true;
    }), [allRows, f, tasks, hits, taskItems]);
    const view = useMemo(() => rows
      .slice().sort((a, b) => b.year - a.year || a.month - b.month || a.paper.localeCompare(b.paper) || a.q - b.q)
      .map((r) => ({ ...r, season: MONTH[r.month] || r.month + ' 月', qn: 'Q' + r.q })), [rows]);

    useEffect(() => { if (hits && hits.code && rows.length === 1) setFocus(rows[0].id); }, [hits, rows]);

    // counts beside the conditions: questions in the year range that match the search
    const counts = useMemo(() => {
      const comp = {}, topic = {};
      allRows.forEach((r) => {
        if (r.year < f.from || r.year > f.to || (hits && hits.ids && !hits.ids.has(r.id))) return;
        comp[r.component] = (comp[r.component] || 0) + 1;
        if (f.components.has(r.component) && r.topic) topic[r.topic] = (topic[r.topic] || 0) + 1;
      });
      return { comp, topic };
    }, [allRows, f.from, f.to, f.components, hits]);

    // the selection and the detail only hold questions the table shows
    useEffect(() => {
      const shown = new Set(view.map((r) => r.id));
      setSelected((s) => (s.every((id) => shown.has(id)) ? s : s.filter((id) => shown.has(id))));
      setFocus((q) => (q && !shown.has(q) ? null : q));
    }, [view]);
    const picked = view.filter((r) => selected.includes(r.id));

    const topicItems = meta.topics.filter((t) => f.components.has(t.component)).map((t) => ({ ...t, n: counts.topic[t.value] || 0 }));
    const compItems = meta.components.map((c) => ({ ...c, n: counts.comp[c.value] || 0 }));
    const years = meta.years.map((y) => ({ value: String(y), label: String(y) }));
    const exams = metas.map((m) => ({ value: m.exam, label: m.label }));

    return h('div', { className: 'dm-row' },
      h('aside', { className: 'dm-cond', 'aria-label': '查询条件' },
        h(E.Select, { label: '考试', options: exams, value: exam, onChange: changeExam }),
        h(Facet, { title: '卷别', items: compItems, picked: f.components, onChange: setComponents, grid: meta.components.length > 2 }),
        h('section', { style: { display: 'flex', flexDirection: 'column', gap: 8 } },
          h('div', { className: 'fx-head' }, h('span', { className: 'fs-small', style: { fontFamily: 'var(--font-medium)' } }, '年份')),
          h('div', { className: 'years' },
            h(E.Select, { ariaLabel: '起始年份', options: years, value: String(f.from), onChange: (v) => setF({ ...f, from: +v }) }),
            h('span', null, '至'),
            h(E.Select, { ariaLabel: '结束年份', options: years, value: String(f.to), onChange: (v) => setF({ ...f, to: +v }) }))),
        topicItems.length ? h(Facet, { title: '主题', items: topicItems, picked: f.topics, onChange: (s) => setF({ ...f, topics: s }) }) : null,
        taskItems.length ? h(Facet, { title: '小问类型', items: taskItems, picked: tasks, onChange: (s) => setF({ ...f, tasks: s }) }) : null),
      h('main', { className: 'dm-results' },
        h('div', { className: 'headline' },
          h('b', null, view.length), h('span', null, '题'), h('b', null, sum(rows)), h('span', null, '分'),
          search ? h('button', { type: 'button', className: 'search-chip', onClick: clearSearch, 'aria-label': '清除搜索' },
            h(E.Icon, { name: 'i-search', size: 'sm' }), h('span', null, search), h(E.Icon, { name: 'i-close', size: 'sm' })) : null),
        h('div', { className: 'selbar' },
          h('div', { className: 'dm-meta', style: { flexGrow: 1 } },
            h('span', null, '已选 ', h('b', null, picked.length), ' 题'), h('span', null, h('b', null, sum(picked)), ' 分')),
          h(E.Button, { variant: 'primary', size: 'sm', icon: 'i-plus', disabled: !picked.length, onClick: () => setAdding(true) }, '加入题组')),
        h('div', { className: 'dm-tablebox' },
          allRows.length ? h(SelTable, {
            ariaLabel: '题目', rows: view, selected, onSelectedChange: setSelected, onActivate: setFocus, minWidth: 460,
            columns: [
              { key: 'year', label: '年份', kind: 'id', width: 88 },
              { key: 'season', label: '考季', kind: 'id', width: 72, sortValue: (r) => r.month },
              { key: 'paper', label: '卷号', kind: 'id', width: 64 },
              { key: 'qn', label: '题号', kind: 'id', sortValue: (r) => r.q },
              { key: 'parts', label: '小问数', kind: 'number', width: 104 },
              { key: 'marks', label: '分值', kind: 'number', unit: '分', width: 88 },
            ],
          }) : h(E.Loading, { label: '读取题目' }),
          allRows.length && !view.length ? h(E.EmptyState, { icon: 'i-search', title: '没有符合条件的题目' }) : null)),
      h(Detail, { qid: focus, onAdd: (id) => { setSelected((s) => (s.includes(id) ? s : s.concat(id))); setAdding(true); } }),
      adding ? h(AddDialog, {
        sets, toast, ids: picked.length ? picked.map((r) => r.id) : (focus ? [focus] : []),
        name: wholePaper(picked, allRows) || queryName(meta, { ...f }),
        source: wholePaper(picked, allRows) ? 'paper' : 'query',
        onClose: () => setAdding(false), onDone: () => { setAdding(false); reloadSets(); },
      }) : null);
  }

  function AddDialog({ sets, ids, name, source, onClose, onDone, toast }) {
    const [target, setTarget] = useState('new');
    const [title, setTitle] = useState(name);
    const options = [{ value: 'new', label: '新建题组' }].concat(sets.map((s) => ({ value: s.id, label: s.name })));
    const confirm = () => {
      const req = target === 'new'
        ? send('POST', '/api/sets', { name: title, items: ids, source })
        : send('PATCH', '/api/sets/' + target, { add: ids });
      req.then((s) => { toast('success', `${ids.length} 题已加入 ${s.name}`); onDone(); })
        .catch((e) => toast('error', e.message));
    };
    return h(E.Dialog, { open: true, onClose, title: '加入题组', confirmLabel: '加入题组', onConfirm: confirm },
      h('div', { className: 'dlg-stack' },
        h(E.Select, { label: '题组', options, value: target, onChange: setTarget }),
        target === 'new' ? h(E.TextField, { label: '名称', value: title, onChange: (e) => setTitle(e.target.value) }) : null));
  }

  // ------------------------------------------------------------------ detail panel

  function Detail({ qid, onAdd }) {
    const [d, setD] = useState(null);
    const [crop, setCrop] = useState('compact');
    const [tab, setTab] = useState('ms');
    useEffect(() => { setD(null); if (qid) api('/api/question/' + qid).then(setD); }, [qid]);
    if (!qid) return h('aside', { className: 'detail' },
      h('div', { className: 'detail-body' }, h(E.EmptyState, { icon: 'i-list', title: '没有选中的题目' })));
    if (!d) return h('aside', { className: 'detail' }, h('div', { className: 'detail-body' }, h(E.Loading, null)));
    const img = crop === 'space' && d.image_space ? d.image_space : d.image;
    const hasEx = d.explanation && d.explanation.parts && d.explanation.parts.length;
    const tabs = [{ value: 'ms', label: d.scheme ? '评分细则' : '答案与解析' }, { value: 'text', label: '题干' },
      { value: 'ex', label: '详解', disabled: !hasEx }];
    return h('aside', { className: 'detail' },
      h('div', { className: 'detail-head' },
        h('div', { className: 'detail-title' },
          h('h2', null, h('span', null, d.code), h('span', null, 'Q' + d.q)),
          h(E.IconButton, { icon: 'i-plus', label: '加入题组', variant: 'ghost', size: 'sm', onClick: () => onAdd(d.id) }),
          d.paper_pdf ? h(E.IconButton, { icon: 'i-doc', label: '打开原卷', variant: 'ghost', size: 'sm',
            onClick: () => open(`/paper/${d.id}#page=${(d.pages[0] || 0) + 1}`, '_blank') }) : null),
        h('div', { className: 'tags' },
          d.topic ? h(E.Tag, { size: 'sm' }, `${d.topic} ${d.topic_name}`) : null,
          h(E.Tag, { size: 'sm' }, `${d.marks} 分`),
          d.diagram ? h(E.Tag, { size: 'sm' }, '有图形') : null)),
      h('div', { className: 'detail-media' },
        d.image_space ? h(E.SegmentedControl, { ariaLabel: '题图', value: crop, onChange: setCrop,
          options: [{ value: 'compact', label: '仅题目' }, { value: 'space', label: '含答题区' }] }) : null,
        img ? h('div', { className: 'qimg' }, h('img', { src: img.src, alt: `${d.code} 第 ${d.q} 题题图` })) : null),
      h('div', { className: 'detail-tabs' },
        h(E.Tabs, { variant: 'line', items: tabs, value: tab, onChange: setTab, ariaLabel: '题目资料' })),
      h('div', { className: 'detail-body' },
        tab === 'ms' ? (d.scheme ? h(Scheme, { rows: d.scheme }) : h(Markdown, { text: d.solution })) : null,
        tab === 'text' ? h(Tex, { tag: 'div', className: 'dm-prose', text: d.text }) : null,
        tab === 'ex' && hasEx ? d.explanation.parts.map((p, i) => h(ExPart, { key: i, p })) : null));
  }

  function Scheme({ rows }) {
    if (!rows.length) return h('span', { className: 'empty-note' }, '没有评分细则');
    return h('div', { className: 'ms' }, rows.map((r, i) => [
      r.part ? h('span', { className: 'p', key: 'p' + i }, r.part) : null,
      h('span', { className: 'c', key: 'c' + i }, r.code),
      h(Tex, { className: 'a', key: 'a' + i, text: r.answer }),
      r.guide ? h(Tex, { className: 'g', key: 'g' + i, text: r.guide }) : null,
    ]));
  }

  function ExPart({ p }) {
    return h('div', { className: 'ex-part' },
      h('h4', null, p.label || '解答'),
      p.approach ? h(Tex, { tag: 'div', className: 'dm-prose', text: p.approach }) : null,
      p.points && p.points.length ? h('div', { className: 'ms' }, p.points.map((pt, i) => [
        h('span', { className: 'c', key: 'c' + i }, pt.mark),
        h(Tex, { className: 'a', key: 'a' + i, text: pt.point }),
        pt.why ? h(Tex, { className: 'g', key: 'g' + i, text: pt.why }) : null,
      ])) : null,
      p.pitfalls && p.pitfalls.length ? h('ul', null, p.pitfalls.map((x, i) => h('li', { key: i }, h(Tex, { text: x })))) : null);
  }

  // ------------------------------------------------------------------ sets page

  /** A heading edited in place: the pencil (or a double click) turns it into a field;
      Enter or leaving the field saves, Escape restores the old name. */
  function EditableTitle({ value, onSave, editing, setEditing, label, small, readOnly }) {
    const ref = useRef(null);
    const [text, setText] = useState(value);
    const start = () => { setText(value); setEditing(true); };   // the field opens holding the current name, selected
    const done = (keep) => {
      setEditing(false);
      const t = text.trim();
      if (keep && t && t !== value) onSave(t);
    };
    if (editing && !readOnly) return h('input', { ref, className: 'title-edit' + (small ? ' sm' : ''), value: text, 'aria-label': label, maxLength: 120,
      autoFocus: true, onFocus: (e) => e.target.select(),
      onChange: (e) => setText(e.target.value), onBlur: () => done(true),
      onKeyDown: (e) => { if (e.key === 'Enter') e.target.blur(); else if (e.key === 'Escape') { setText(value); setEditing(false); } } });
    return h('div', { className: 'title-row' + (small ? ' sm' : '') },
      h('h1', { onDoubleClick: readOnly ? undefined : start, style: readOnly ? { cursor: 'default' } : undefined }, value),
      readOnly ? null : h(E.IconButton, { icon: 'i-edit', label, variant: 'ghost', size: 'sm', onClick: start }));
  }

  let nameNext = null;   // a set just made: its page opens with the name being edited

  const SOURCE_ICON = { query: 'i-search', paper: 'i-doc', import: 'i-upload', manual: 'i-list' };

  function SetsPage({ sets, current, reloadSets, templates, toast, acts }) {
    const s = sets.find((x) => x.id === current) || sets[0];
    const fileRef = useRef(null);
    const importFile = (e) => {
      const file = e.target.files[0];
      e.target.value = '';
      if (!file) return;
      file.text().then((t) => send('POST', '/api/sets/import', JSON.parse(t)))
        .then((n) => {
          toast(n.unknown && n.unknown.length ? 'warning' : 'success',
            n.unknown && n.unknown.length ? `${n.count} 题已导入,${n.unknown.length} 个编号在题库中找不到` : `${n.count} 题已导入`);
          reloadSets(); location.hash = '#/sets/' + n.id;
        })
        .catch((err) => toast('error', err.message || '无法读取这个文件'));
    };
    const create = () => send('POST', '/api/sets', { name: '新题组', items: [] })
      .then((n) => { nameNext = n.id; reloadSets(); location.hash = '#/sets/' + n.id; });
    return h('div', { className: 'dm-row' },
      h(TopActs, { el: acts },
        act('i-plus', '新建题组', create),
        act('i-upload', '导入 JSON', () => fileRef.current.click())),
      h('aside', { className: 'setlist' },
        h('input', { ref: fileRef, type: 'file', accept: '.json,application/json', className: 'hidden-input', onChange: importFile }),
        sets.length ? h(E.List, {
          variant: 'two-line', selectable: true, ariaLabel: '题组', value: s ? s.id : undefined,
          onChange: (v) => { location.hash = '#/sets/' + v; },
          items: sets.map((x) => ({ value: x.id, icon: SOURCE_ICON[x.source] || 'i-list', title: x.name, subtitle: `${x.count} 题 ${x.marks} 分` })),
        }) : h(E.EmptyState, { icon: 'i-list', title: '还没有题组' })),
      s ? h(SetDetail, { key: s.id, s, reloadSets, templates, toast }) : h('main', { className: 'setmain' }));
  }

  function SetDetail({ s, reloadSets, templates, toast }) {
    const [rows, setRows] = useState(null);
    const [selected, setSelected] = useState([]);
    const [renaming, setRenaming] = useState(() => nameNext === s.id);
    const [deleting, setDeleting] = useState(false);
    useEffect(() => { if (nameNext === s.id) nameNext = null; }, []);

    useEffect(() => {
      const exams = [...new Set(s.items.map((q) => (/^\d{4}_/.test(q) ? q.slice(0, 4) : q.split('-')[0])))];
      Promise.all(exams.map((e) => api('/api/questions?exam=' + e))).then((lists) => {
        const by = {};
        lists.flat().forEach((r) => { by[r.id] = r; });
        setRows(by);
      });
    }, [s.id]);

    const items = s.items.filter((q) => rows && rows[q]);
    const view = items.map((q, i) => {
      const r = rows[q];
      return { ...r, n: String(i + 1).padStart(2, '0'), season: MONTH[r.month] || r.month + ' 月', qn: 'Q' + r.q };
    });
    const save = (body) => send('PATCH', '/api/sets/' + s.id, body).then(reloadSets).catch((e) => toast('error', e.message));
    const move = (d) => {
      const list = s.items.slice();
      const idx = selected.map((q) => list.indexOf(q)).sort((a, b) => (d < 0 ? a - b : b - a));
      for (const i of idx) {
        const j = i + d;
        if (j < 0 || j >= list.length || selected.includes(list[j])) continue;
        [list[i], list[j]] = [list[j], list[i]];
      }
      save({ items: list });
    };
    const remove = () => { save({ items: s.items.filter((q) => !selected.includes(q)) }); setSelected([]); };

    return h(React.Fragment, null, h('main', { className: 'setmain' },
      h('div', { className: 'page-head' },
        h('div', { className: 'title-line' },
          h(EditableTitle, { value: s.name, editing: renaming, setEditing: setRenaming, label: '重命名题组', onSave: (name) => save({ name }) }),
          h(MoreMenu, { label: '更多操作', items: [
            { label: '导出 JSON', onClick: () => { location.href = `/api/sets/${s.id}/export`; } },
            { label: '删除题组', danger: true, onClick: () => setDeleting(true) }] })),
        h('div', { className: 'dm-toolbar' },
          h('div', { className: 'dm-meta dm-grow' },
            h('span', null, h('b', null, s.count), ' 题'), h('span', null, h('b', null, s.marks), ' 分'),
            h('span', { className: 't' }, s.created)),
          act('k-up', '上移题目', () => move(-1), { disabled: !selected.length }),
          act('k-down', '下移题目', () => move(1), { disabled: !selected.length }),
          act('i-trash', '移出题组', remove, { disabled: !selected.length }))),
      h('div', { className: 'dm-tablebox' },
        !rows ? h(E.Loading, null) : view.length ? h(SelTable, {
          ariaLabel: '题组中的题目', rows: view, selected, onSelectedChange: setSelected, minWidth: 440,
          columns: [
            { key: 'n', label: '序号', kind: 'id', width: 80 },
            { key: 'year', label: '年份', kind: 'id', width: 72, sortable: false },
            { key: 'season', label: '考季', kind: 'id', width: 72, sortable: false },
            { key: 'paper', label: '卷号', kind: 'id', width: 64, sortable: false },
            { key: 'qn', label: '题号', kind: 'id', sortable: false },
            { key: 'marks', label: '分值', kind: 'number', unit: '分', width: 80, sortable: false },
          ],
        }) : h(E.EmptyState, { icon: 'i-list', title: '题组中还没有题目', description: '在查询页选中题目后加入题组' })),
      deleting ? h(E.Dialog, { open: true, danger: true, title: '删除题组', confirmLabel: '删除题组', onClose: () => setDeleting(false),
        onConfirm: () => send('DELETE', '/api/sets/' + s.id).then(() => { location.hash = '#/sets'; reloadSets(); }) },
      h('p', null, `删除后 ${s.name} 将无法恢复。题库中的题目不受影响。`)) : null),
    h(SetPanel, { s, templates, toast }));
  }


  const download = (url) => { const a = document.createElement('a'); a.href = url; a.download = ''; document.body.appendChild(a); a.click(); a.remove(); };

  const fetchFile = (url, body, toast) => fetch(url, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) })
    .then((r) => { if (!r.ok) throw new Error(r.statusText); return Promise.all([r.blob(), r.headers.get('Content-Disposition') || '']); })
    .then(([b, disp]) => {
      const m = disp.match(/filename\*=UTF-8''([^;]+)/);
      const a = document.createElement('a');
      a.href = URL.createObjectURL(b);
      a.download = m ? decodeURIComponent(m[1]) : '';
      document.body.appendChild(a); a.click(); a.remove();
      setTimeout(() => URL.revokeObjectURL(a.href), 1000);
    })
    .catch((e) => toast('error', e.message));

  function SetPanel({ s, templates, toast }) {
    const [pages, setPages] = useState(null);
    const [tid, setTid] = useState('default');
    const [boards, setBoards] = useState(null);
    useEffect(() => {
      setPages(null);
      if (s.count) api(`/api/sets/${s.id}/paper`).then((p) => setPages(p.pages)).catch(() => setPages(0));
    }, [s.id, s.items.join(), s.name]);
    useEffect(() => { api(`/api/sets/${s.id}/boards`).then(setBoards).catch(() => setBoards(null)); }, [s.id, s.items.join()]);
    const openBoard = () => send('POST', `/api/sets/${s.id}/board`).then((b) => { location.href = '/write/' + b.id; })
      .catch((e) => toast('error', e.message));
    const docRow = (label, kind, n) => h('div', { className: 'panel-row' },
      h('span', { className: 'fs-small', style: { flexGrow: 1 } }, label),
      h('span', { className: 'dm-meta', style: { fontSize: 12 } }, h('span', null, h('b', null, n), ' 题')),
      act('i-doc', '下载' + label, () => download(`/doc/${s.id}/${kind}?download=1`), { disabled: !n }),
      act('i-arrow-r', '打开' + label, () => open(`/doc/${s.id}/${kind}`, '_blank'), { disabled: !n }));
    return h('aside', { className: 'setpanel' },
      h('section', null,
        h('div', { className: 'panel-row' },
          h('h2', { className: 'fs-lead panel-title' }, '题目卷'),
          pages != null ? h('span', { className: 'dm-meta' }, h('span', null, h('b', null, pages), ' 页')) : null,
          act('i-doc', '下载 PDF', () => download(`/api/sets/${s.id}/paper.pdf`), { disabled: !s.count || pages == null }),
          act('i-edit', '打开白板', openBoard, { disabled: !s.count || pages == null }),
          act('i-arrow-r', '打开题目卷', () => { location.hash = `#/sets/${s.id}/paper`; }, { disabled: !s.count })),
        boards && (boards.boards.length || boards.answers) ? h('div', { className: 'panel-sub' },
          boards.boards.length ? h(React.Fragment, null,
            h('span', { className: 'fs-small panel-sub-title' }, '白板'),
            boards.boards.map((b) => h('div', { key: b.id, className: 'panel-row' },
              h('div', { className: 'dm-meta', style: { flexGrow: 1, fontSize: 12 } }, h('span', { className: 't' }, b.updated), h('span', null, h('b', null, b.pages), ' 页')),
              h(E.IconButton, { icon: 'i-doc', label: '导出作答 PDF', variant: 'ghost', size: 'sm', tooltip: 'below',
                onClick: () => fetchFile(`/api/boards/${b.id}/export`, {}, toast).then(() => api(`/api/sets/${s.id}/boards`).then(setBoards)) }),
              h(E.IconButton, { icon: 'i-arrow-r', label: '打开白板', variant: 'ghost', size: 'sm', tooltip: 'below', onClick: () => { location.href = '/write/' + b.id; } })))) : null,
          boards.answers ? h(React.Fragment, null,
            h('span', { className: 'fs-small panel-sub-title' }, '作答 PDF'),
            h('div', { className: 'panel-row' },
              h('div', { className: 'dm-meta', style: { flexGrow: 1, fontSize: 12 } }, h('span', { className: 't' }, boards.answers.updated), h('span', null, h('b', null, boards.answers.pages), ' 页')),
              h(E.IconButton, { icon: 'i-doc', label: '下载作答 PDF', variant: 'ghost', size: 'sm', tooltip: 'below', onClick: () => download(`/api/sets/${s.id}/answers.pdf`) }))) : null) : null),
      h('section', null,
        h('div', { className: 'panel-row' }, h('h2', { className: 'fs-lead panel-title' }, '评分细则与详解')),
        docRow('评分细则', 'scheme', s.docs.scheme),
        docRow('详解', 'explanation', s.docs.explanation)),
      h('section', null,
        h('div', { className: 'panel-row' },
          h('h2', { className: 'fs-lead panel-title' }, '导出'),
          act('i-box', '下载 ZIP', () => downloadZip(s, { template: tid }, toast), { disabled: !s.count }),
          act('i-sliders', '打开导出页', () => { location.hash = `#/sets/${s.id}/export/${tid}`; })),
        h(E.Select, { ariaLabel: '导出模板', options: templates.map((t) => ({ value: t.id, label: t.name })), value: tid, onChange: setTid })));
  }

  function PaperPage({ s }) {
    const [info, setInfo] = useState(null);
    const [page, setPage] = useState(1);
    const per = 3;
    useEffect(() => { api(`/api/sets/${s.id}/paper`).then(setInfo); }, [s.id]);
    const first = (page - 1) * per;
    const shown = info ? Array.from({ length: Math.min(per, info.pages - first) }, (_, i) => first + i) : [];
    return h('main', { className: 'paperpage' },
      h('div', { className: 'paper-head' },
        h('div', { className: 'page-head', style: { flexGrow: 1 } },
          h('h1', { className: 'page-title' }, s.name),
          h('div', { className: 'dm-meta' }, h('span', null, h('b', null, s.count), ' 题'), h('span', null, h('b', null, s.marks), ' 分'),
            info ? h('span', null, h('b', null, info.pages), ' 页') : null)),
        info && info.pages > per ? h(E.Pagination, { total: info.pages, pageSize: per, page, onChange: setPage, variant: 'simple' }) : null,
        h(E.Button, { variant: 'primary', size: 'md', icon: 'i-doc', disabled: !info, onClick: () => download(`/api/sets/${s.id}/paper.pdf`) }, '下载 PDF')),
      info ? h('div', { className: 'sheets' }, shown.map((n) => h('img', { key: n + '-' + s.items.join(), className: 'sheet', src: `/api/sets/${s.id}/paper/${n}.png`, alt: `第 ${n + 1} 页` })))
        : h(E.Loading, { label: '生成题目卷' }));
  }

  // ------------------------------------------------------------------ export (F7) and templates (F8)

  const IMG = ['image', 'image_with_space'];
  const optsOf = (st) => {
    const per = st.per_question;
    return {
      image: per.some((k) => IMG.includes(k)), text: per.includes('text'), space: !per.includes('image'),
      ms: per.includes('mark_scheme'), ex: per.includes('explanation'),
      answers: st.answers === 'written_pdf', layout: st.layout, readme: !!st.prompt_file,
    };
  };
  const settingsOf = (st, o) => {
    const per = [];
    if (o.image) per.push(o.space ? 'image_with_space' : 'image');
    if (o.text) per.push('text');
    if (o.ms) per.push('mark_scheme');
    if (o.ex) per.push('explanation');
    return { ...st, per_question: per, answers: o.answers ? 'written_pdf' : 'none', layout: o.layout,
      prompt_file: o.readme ? (st.prompt_file || 'README.md') : '' };
  };
  const sizeText = (n) => (n >= 1048576 ? (n / 1048576).toFixed(1) + ' MB' : Math.max(1, Math.round(n / 1024)) + ' KB');

  /** What each question carries under a template, for the template list. */
  function contents(settings) {
    const o = optsOf(settings);
    return [o.image && '题图', o.text && '题干文字', o.ms && '评分细则', o.ex && '详解', o.answers && '作答 PDF'].filter(Boolean).join('、');
  }

  function ExportOptions({ settings, onChange }) {
    const o = optsOf(settings);
    const set = (k, v) => onChange(settingsOf(settings, { ...o, [k]: v }));
    const box = (k, label, lock) => h(E.Checkbox, { checked: o[k], onChange: () => { if (!(lock && o[k])) set(k, !o[k]); } }, label);
    return h(React.Fragment, null,
      h('fieldset', { className: 'opt-group ex' }, h('legend', null, '题目'),
        box('image', '题图', !o.text), box('text', '题干文字', !o.image)),
      h('fieldset', { className: 'opt-group ex' }, h('legend', null, '题图范围'),
        h(E.Radio, { name: 'crop', checked: !o.space, disabled: !o.image, onChange: () => set('space', false) }, '仅题目'),
        h(E.Radio, { name: 'crop', checked: o.space, disabled: !o.image, onChange: () => set('space', true) }, '含答题区')),
      h('fieldset', { className: 'opt-group ex' }, h('legend', null, '附加'),
        box('ms', '评分细则'), box('ex', '详解'), box('answers', '作答 PDF')),
      h('fieldset', { className: 'opt-group ex' }, h('legend', null, '文件结构'),
        h(E.Radio, { name: 'layout', checked: o.layout === 'folder_per_question', onChange: () => set('layout', 'folder_per_question') }, '每题一个文件夹'),
        h(E.Radio, { name: 'layout', checked: o.layout === 'flat', onChange: () => set('layout', 'flat') }, '全部放在同一层')),
      h('fieldset', { className: 'opt-group ex' }, h('legend', null, '说明文件'), box('readme', 'README.md')));
  }

  /** The README as the export writes it: headings, paragraphs, code blocks, tables. */
  function MdView({ text }) {
    const lines = (text || '').split('\n');
    const out = [];
    for (let i = 0; i < lines.length; i++) {
      const l = lines[i];
      if (/^```/.test(l)) {
        const code = [];
        for (i++; i < lines.length && !/^```/.test(lines[i]); i++) code.push(lines[i]);
        out.push(h('pre', { key: i, className: 'md-code' }, code.join('\n')));
      } else if (/^\s*\|/.test(l)) {
        const rows = [];
        for (; i < lines.length && /^\s*\|/.test(lines[i]); i++) {
          if (!/^\s*\|[\s|:-]+\|\s*$/.test(lines[i])) rows.push(lines[i].trim().replace(/^\||\|$/g, '').split('|').map((c) => c.trim()));
        }
        i--;
        out.push(h('table', { key: i, className: 'md-table' },
          h('thead', null, h('tr', null, (rows[0] || []).map((c, j) => h('th', { key: j }, c)))),
          h('tbody', null, rows.slice(1).map((r, k) => h('tr', { key: k }, r.map((c, j) => h('td', { key: j }, c)))))));
      } else if (/^#{1,4} /.test(l)) {
        const n = l.match(/^#+/)[0].length;
        out.push(h('h' + Math.min(n + 1, 4), { key: i, className: n === 1 ? 'fs-h3' : 'fs-lead' }, l.replace(/^#+ /, '')));
      } else if (l.trim()) {
        out.push(h(Tex, { key: i, tag: 'p', className: 'fs-body', text: l }));
      }
    }
    return h('article', { className: 'md-view' }, out);
  }

  function FileTree({ files }) {
    const seen = new Set();
    const out = [];
    files.forEach((f) => {
      const k = f.path.lastIndexOf('/');
      if (k > 0) {
        const dir = f.path.slice(0, k);
        if (!seen.has(dir)) { seen.add(dir); out.push(h('div', { key: 'd' + dir, className: 'tree-row' }, h('span', null, dir))); }
        out.push(h('div', { key: f.path, className: 'tree-row in' }, h('span', null, f.path.slice(k + 1)), h('span', null, sizeText(f.size))));
      } else out.push(h('div', { key: f.path, className: 'tree-row' }, h('span', null, f.path), h('span', null, sizeText(f.size))));
    });
    return h('div', { className: 'tree' }, out);
  }

  function downloadZip(s, body, toast) {
    return fetch(`/api/sets/${s.id}/zip`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) })
      .then((r) => { if (!r.ok) throw new Error(r.statusText); return r.blob(); })
      .then((b) => {
        const a = document.createElement('a');
        a.href = URL.createObjectURL(b);
        a.download = s.name.replace(/[/\\:]/g, '-') + '.zip';
        document.body.appendChild(a); a.click(); a.remove();
        setTimeout(() => URL.revokeObjectURL(a.href), 1000);
      })
      .catch((e) => toast('error', e.message));
  }

  function usePreview(s, st, body) {
    const [pv, setPv] = useState(null);
    useEffect(() => {
      if (!s || !st) return undefined;
      const t = setTimeout(() => send('POST', `/api/sets/${s.id}/zip/preview`, { settings: st, body }).then(setPv).catch(() => setPv(null)), 200);
      return () => clearTimeout(t);
    }, [s && s.id, s && s.items.join(), JSON.stringify(st), body]);
    return pv;
  }

  function ExportPage({ s, tid, templates, reloadTemplates, toast, acts }) {
    const [pick, setPick] = useState(tid || 'default');
    const [st, setSt] = useState(null);
    const [body, setBody] = useState('');
    const [doc, setDoc] = useState('readme');
    const [saving, setSaving] = useState(false);
    const [name, setName] = useState('');
    useEffect(() => {
      const t = templates.find((x) => x.id === pick);
      if (t) { setSt(t.settings); setBody(t.body); }
    }, [pick, templates]);
    const pv = usePreview(s, st, body);
    const copy = () => navigator.clipboard.writeText(pv.readme).then(() => toast('success', '已复制 README'), () => toast('error', '无法复制'));
    const saveAs = () => send('POST', '/api/templates', { name, settings: st, body })
      .then((t) => { toast('success', `已保存为 ${t.name}`); return reloadTemplates().then(() => setPick(t.id)); })
      .catch((e) => toast('error', e.message));
    return h('div', { className: 'dm-row exportpage' },
      h(TopActs, { el: acts },
        h(E.Button, { variant: 'primary', size: 'md', icon: 'i-box', disabled: !st || !s.count, onClick: () => downloadZip(s, { settings: st, body }, toast) }, '下载 ZIP')),
      h('aside', { className: 'ex-side' },
        h('div', { className: 'page-head' },
          h('h1', { className: 'page-title' }, s.name),
          h('div', { className: 'dm-meta' }, h('span', null, h('b', null, s.count), ' 题'), h('span', null, h('b', null, s.marks), ' 分'))),
        h('div', { className: 'field-act' },
          h(E.Select, { label: '模板', options: templates.map((t) => ({ value: t.id, label: t.name })), value: pick, onChange: setPick }),
          act('i-plus', '另存为模板', () => { setName(''); setSaving(true); }, { disabled: !st })),
        st ? h(ExportOptions, { settings: st, onChange: setSt }) : null),
      h('section', { className: 'ex-files' },
        h('div', { className: 'panel-row' },
          h('h2', { className: 'fs-lead', style: { margin: 0, flexGrow: 1 } }, '文件'),
          pv ? h('div', { className: 'dm-meta', style: { fontSize: 12 } }, h('span', null, h('b', null, pv.files.length), ' 个'), h('span', null, sizeText(pv.size))) : null),
        pv ? h(FileTree, { files: pv.files }) : h(E.Loading, null)),
      h('section', { className: 'ex-doc' },
        h('div', { className: 'panel-row' },
          h(E.Tabs, { variant: 'line', value: doc, onChange: setDoc, ariaLabel: '压缩包文件',
            items: [{ value: 'readme', label: (st && st.prompt_file) || 'README.md' }, { value: 'manifest', label: 'manifest.json' }] }),
          h('span', { className: 'dm-grow' }),
          act('i-copy', '复制 README', copy, { disabled: !pv })),
        h('div', { className: 'ex-docbody' },
          !pv ? h(E.Loading, null) : doc === 'readme' ? h(MdView, { text: pv.readme }) : h('pre', { className: 'md-code' }, pv.manifest))),
      saving ? h(E.Dialog, { open: true, title: '另存为模板', confirmLabel: '保存模板', onClose: () => setSaving(false), onConfirm: saveAs },
        h(E.TextField, { label: '名称', value: name, onChange: (e) => setName(e.target.value) })) : null);
  }

  const HOLES = [
    ['{title}', '题组名称'], ['{count}', '题数'], ['{total_marks}', '总分'], ['{papers}', '试卷'],
    ['{date}', '日期'], ['{question_table}', '题目表'], ['{file_tree}', '目录'],
  ];

  function TemplatesPage({ templates, current, reloadTemplates, sets, toast, acts }) {
    const t = templates.find((x) => x.id === current) || templates[0];
    const [name, setName] = useState('');
    const [st, setSt] = useState(null);
    const [body, setBody] = useState('');
    const [tab, setTab] = useState('src');
    const [sid, setSid] = useState(sets[0] ? sets[0].id : '');
    const [deleting, setDeleting] = useState(false);
    const [renaming, setRenaming] = useState(false);
    const area = useRef(null);
    useEffect(() => { if (t) { setName(t.name); setSt(t.settings); setBody(t.body); } }, [t && t.id, templates.length]);
    // changes are saved as they are made (built-in templates are read-only)
    useEffect(() => {
      if (!t || t.builtin || !st) return undefined;
      if (name === t.name && body === t.body && JSON.stringify(st) === JSON.stringify(t.settings)) return undefined;
      const id = t.id;
      const tm = setTimeout(() => send('PUT', '/api/templates/' + id, { name, settings: st, body })
        .then(() => reloadTemplates()).catch((e) => toast('error', e.message)), 600);
      return () => clearTimeout(tm);
    }, [name, body, JSON.stringify(st)]);
    useEffect(() => { if (!sid && sets[0]) setSid(sets[0].id); }, [sets.length]);
    const pv = usePreview(tab === 'preview' ? sets.find((x) => x.id === sid) : null, st, body);
    if (!t || !st) return h('div', { className: 'dm-row' }, h(E.Loading, null));
    const go = (id) => { location.hash = '#/templates/' + id; };
    const create = () => send('POST', '/api/templates', { name: '导出模板', settings: templates[0].settings, body: templates[0].body })
      .then((n) => reloadTemplates().then(() => go(n.id)));
    const copy = () => send('POST', '/api/templates', { name: name + ' 副本', settings: st, body }).then((n) => reloadTemplates().then(() => go(n.id)));
    const insert = (v) => {
      const el = area.current;
      const a = el ? el.selectionStart : body.length;
      const b = el ? el.selectionEnd : body.length;
      setBody(body.slice(0, a) + v + body.slice(b));
      requestAnimationFrame(() => { if (el) { el.focus(); el.selectionStart = el.selectionEnd = a + v.length; } });
    };
    return h('div', { className: 'dm-row tplpage' },
      h(TopActs, { el: acts }, act('i-plus', '新建导出模板', create)),
      h('aside', { className: 'tpl-list' },
        h(KindTabs, { value: 'export' }),
        h(E.List, { variant: 'two-line', selectable: true, ariaLabel: '导出模板', value: t.id, onChange: go,
          items: templates.map((x) => ({ value: x.id, icon: 'i-doc', title: x.name, subtitle: contents(x.settings) })) })),
      h('section', { className: 'tpl-opts' },
        h('div', { className: 'title-line' },
          h(EditableTitle, { value: name, small: true, readOnly: t.builtin, editing: renaming, setEditing: setRenaming, label: '重命名模板', onSave: setName }),
          h(MoreMenu, { label: '更多操作', items: [
            { label: '复制模板', onClick: copy },
            t.builtin ? null : { label: '删除模板', danger: true, onClick: () => setDeleting(true) }] })),
        t.builtin ? h('p', { className: 'lock-note' }, '内置模板不可修改，复制模板后可修改副本') : null,
        h('div', { className: t.builtin ? 'opts locked' : 'opts' }, h(ExportOptions, { settings: st, onChange: t.builtin ? () => {} : setSt }))),
      h('section', { className: 'tpl-edit' },
        h('div', { className: 'panel-row', style: { gap: 'var(--head)' } },
          h(E.Tabs, { variant: 'line', value: tab, onChange: setTab, ariaLabel: '说明文件',
            items: [{ value: 'src', label: st.prompt_file || 'README.md' }, { value: 'preview', label: '预览' }] }),
          h('span', { className: 'dm-grow' }),
          tab === 'src'
            ? (t.builtin ? null : h('div', { style: { width: 176 } }, h(E.Select, { ariaLabel: '插入占位符', placeholder: '插入占位符', size: 'sm', value: '',
              options: HOLES.map(([v, m]) => ({ value: v, label: v, meta: m })), onChange: insert })))
            : h('div', { style: { width: 280 } }, h(E.Select, { ariaLabel: '预览题组', size: 'sm', value: sid, onChange: setSid,
              options: sets.map((x) => ({ value: x.id, label: x.name })) }))),
        tab === 'src'
          ? h('textarea', { ref: area, className: 'tpl-src', value: body, readOnly: t.builtin, spellCheck: false, onChange: (e) => setBody(e.target.value) })
          : h('div', { className: 'ex-docbody' }, pv ? h(MdView, { text: pv.readme }) : sets.length ? h(E.Loading, null) : h(E.EmptyState, { icon: 'i-list', title: '还没有题组' }))),
      deleting ? h(E.Dialog, { open: true, danger: true, title: '删除模板', confirmLabel: '删除模板', onClose: () => setDeleting(false),
        onConfirm: () => send('DELETE', '/api/templates/' + t.id).then(() => reloadTemplates()).then(() => go('default')) },
      h('p', null, `删除后 ${t.name} 将无法恢复。`)) : null);
  }

  // ------------------------------------------------------------------ batch generation (F9)

  const NW = 168, HEAD = 33, ROW = 28;
  const portY = (n, i) => n.y + HEAD + ROW * i + ROW / 2;
  const nodeRows = (cat, n) => Math.max(cat.nodes[n.type].ins.length, cat.nodes[n.type].outs.length);
  const fieldLabel = (cat, t, k) => ((cat.fields[t] || []).find((f) => f[0] === k) || [k, k])[1];

  function paramText(cat, n, inType, inShape, templates, sets) {
    const p = n.params || {};
    const F = (k) => fieldLabel(cat, inType || 'q', k);
    switch (n.type) {
      case 'bank': return p.exam || '9709';
      case 'book': return ((cat.books.find((b) => b.value === p.book) || {}).label) || p.book || '';
      case 'set': return ((sets.find((s) => s.id === p.set) || {}).name) || '';
      case 'filter': return (p.conds || []).filter((c) => c.field && String(c.value || '').trim()).map((c) => `${F(c.field)} ${c.op} ${c.value}`);
      case 'sort': return p.by === 'random' ? ['随机', `种子 ${p.seed ?? 1}`] : `${F(p.field || 'marks')} ${p.desc ? '降序' : '升序'}`;
      case 'take': return inShape === 'group' ? `每组 ${p.n ?? 10} 条` : `前 ${p.n ?? 10} 条`;
      case 'group': return F(p.field || 'topic');
      case 'merge': return '';
      case 'join': return `${fieldLabel(cat, 'c', p.left || 'topic')} = ${F(p.right || 'topic')}`;
      case 'export': return [((templates.find((t) => t.id === (p.template || 'default')) || {}).name) || '默认'].concat(inShape === 'group' ? ['每组一个文件夹'] : []);
      case 'newset': return p.name || '';
      case 'paper': return '';
      default: return '';
    }
  }

  const TYPE_LABEL = { q: '题目', c: '章节', f: '文件' };
  /** A port's label: what flows through it once known (题目、章节、分组), else the node's own name for it. */
  function portLabel(v, fallback) {
    if (!v || ['左', '右', '附件'].includes(fallback)) return fallback;
    return v.shape === 'group' ? '分组' : TYPE_LABEL[v.type] || fallback;
  }

  function FlowPage({ fid, templates, sets, reloadSets, toast, onTitle }) {
    const [cat, setCat] = useState(null);
    const [g, setG] = useState(null);
    const [saved, setSaved] = useState('');
    const [ev, setEv] = useState(null);
    const [run, setRun] = useState(null);
    const [running, setRunning] = useState(false);
    const [sel, setSel] = useState(null);         // {node} or {link: index}
    const [drag, setDrag] = useState(null);       // a wire being drawn: {from, x, y}
    const box = useRef(null);
    const nid = useRef(1);

    useEffect(() => { api('/api/flows/catalog').then(setCat); }, []);
    // changes are saved as they are made; a built-in flow is saved only as a copy
    useEffect(() => {
      if (!g || g.builtin) return undefined;
      const text = JSON.stringify(g);
      if (text === saved) return undefined;
      const tm = setTimeout(() => send('PUT', '/api/flows/' + g.id, g).then(() => setSaved(text)).catch((e) => toast('error', e.message)), 800);
      return () => clearTimeout(tm);
    }, [g, saved]);
    useEffect(() => {
      setRun(null); setSel(null);
      api('/api/flows/' + fid).then((x) => {
        setG(x); setSaved(JSON.stringify(x));
        nid.current = 1 + Math.max(0, ...x.nodes.map((n) => +(String(n.id).match(/\d+$/) || [0])[0]));
      }).catch(() => setG(false));
    }, [fid]);
    useEffect(() => {
      if (!g) return undefined;
      const t = setTimeout(() => send('POST', '/api/flows/eval', g).then(setEv).catch(() => {}), 250);
      return () => clearTimeout(t);
    }, [g && JSON.stringify({ n: g.nodes.map((n) => [n.id, n.type, n.params]), l: g.links })]);

    const del = useCallback(() => {
      if (!sel || !g) return;
      if (sel.node) setG({ ...g, nodes: g.nodes.filter((n) => n.id !== sel.node), links: g.links.filter((l) => l.from[0] !== sel.node && l.to[0] !== sel.node) });
      else setG({ ...g, links: g.links.filter((_, i) => i !== sel.link) });
      setSel(null);
    }, [sel, g]);
    useEffect(() => {
      const on = (e) => {
        if ((e.key === 'Delete' || e.key === 'Backspace') && !/INPUT|TEXTAREA|SELECT/.test(document.activeElement.tagName)) { e.preventDefault(); del(); }
      };
      addEventListener('keydown', on);
      return () => removeEventListener('keydown', on);
    }, [del]);

    useEffect(() => { if (g && onTitle) onTitle(g.name); }, [g && g.name]);
    if (g === false) return h('div', { className: 'dm-row' }, h(E.EmptyState, { icon: 'i-doc', title: '没有这个流程' }));
    if (!g || !cat) return h('div', { className: 'dm-row' }, h(E.Loading, null));

    const byId = Object.fromEntries(g.nodes.map((n) => [n.id, n]));
    const ports = (ev && ev.ports) || {};
    const errors = (ev && ev.errors) || {};
    const outOf = (id, i) => (ports[id] || [])[i];
    const inOf = (id, i) => { const l = g.links.find((x) => x.to[0] === id && x.to[1] === i); return l ? outOf(l.from[0], l.from[1]) : null; };
    const shapeOf = (id, i) => { const o = outOf(id, i); return o ? o.shape : cat.nodes[byId[id].type].outs[i][1]; };
    const update = (id, patch) => setG({ ...g, nodes: g.nodes.map((n) => (n.id === id ? { ...n, params: { ...n.params, ...patch } } : n)) });

    const add = (type) => {
      const el = box.current;
      const x = (el ? el.scrollLeft : 0) + 32 + (g.nodes.length % 4) * 24;
      const y = (el ? el.scrollTop : 0) + 32 + (g.nodes.length % 4) * 24;
      const id = 'n' + nid.current++;
      const params = { bank: { exam: '9709' }, book: { book: '9709_p1' }, filter: { conds: [{ field: 'year', op: '≥', value: '' }] },
        sort: { by: 'field', field: 'marks', desc: true }, take: { n: 10 }, group: { field: 'topic' },
        join: { left: 'topic', right: 'topic' }, export: { template: 'default' }, newset: { name: g.name },
        set: { set: sets[0] ? sets[0].id : '' } }[type] || {};
      setG({ ...g, nodes: g.nodes.concat([{ id, type, x: Math.round(x), y: Math.round(y), params }]) });
      setSel({ node: id });
    };

    const local = (e) => { const r = box.current.getBoundingClientRect(); return [e.clientX - r.left + box.current.scrollLeft, e.clientY - r.top + box.current.scrollTop]; };
    const startMove = (e, n) => {
      if (e.button !== 0) return;
      e.preventDefault();
      setSel({ node: n.id });
      const [sx, sy] = local(e); const ox = n.x, oy = n.y;
      const move = (ev2) => { const [x, y] = local(ev2); setG((cur) => ({ ...cur, nodes: cur.nodes.map((m) => (m.id === n.id ? { ...m, x: Math.max(8, Math.round(ox + x - sx)), y: Math.max(8, Math.round(oy + y - sy)) } : m)) })); };
      const up = () => { removeEventListener('pointermove', move); removeEventListener('pointerup', up); };
      addEventListener('pointermove', move); addEventListener('pointerup', up);
    };
    const startWire = (e, n, i) => {
      e.preventDefault(); e.stopPropagation();
      const [x, y] = local(e);
      setDrag({ from: [n.id, i], x, y });
      const move = (ev2) => { const [mx, my] = local(ev2); setDrag((d) => d && { ...d, x: mx, y: my }); };
      const up = (ev2) => {
        removeEventListener('pointermove', move); removeEventListener('pointerup', up);
        const t = document.elementFromPoint(ev2.clientX, ev2.clientY);
        const pin = t && t.closest && t.closest('[data-in]');
        setDrag(null);
        if (!pin) return;
        const [to, k] = pin.dataset.in.split(':');
        if (to === n.id) return;
        setG((cur) => ({ ...cur, links: cur.links.filter((l) => !(l.to[0] === to && l.to[1] === +k)).concat([{ from: [n.id, i], to: [to, +k] }]) }));
      };
      addEventListener('pointermove', move); addEventListener('pointerup', up);
    };

    // forward: a curve; backward (into a node to the left): out to the right, along the gap
    // between the two nodes, and in from the left, as in the design
    const wirePath = (x1, y1, x2, y2, a, b) => {
      if (x2 > x1 + 8) { const d = Math.max(32, (x2 - x1) / 2); return `M${x1} ${y1} C${x1 + d} ${y1}, ${x2 - d} ${y2}, ${x2} ${y2}`; }
      let mid = (y1 + y2) / 2;
      if (a && b) {
        const aBottom = a.y + HEAD + ROW * nodeRows(cat, a) + 64, bBottom = b.y + HEAD + ROW * nodeRows(cat, b) + 64;
        mid = b.y > aBottom ? (aBottom + b.y) / 2 : a.y > bBottom ? (bBottom + a.y) / 2 : Math.max(aBottom, bBottom) + 16;
      }
      const r = 8, xo = x1 + 16, xi = x2 - 16, down = mid > y1 ? 1 : -1, back = y2 > mid ? 1 : -1;
      return `M${x1} ${y1} H${xo - r} Q${xo} ${y1} ${xo} ${y1 + r * down} V${mid - r * down} Q${xo} ${mid} ${xo - r} ${mid}` +
        ` H${xi + r} Q${xi} ${mid} ${xi} ${mid + r * back} V${y2 - r * back} Q${xi} ${y2} ${xi + r} ${y2} H${x2}`;
    };
    const W = Math.max(960, ...g.nodes.map((n) => n.x + NW + 240));
    const H = Math.max(560, ...g.nodes.map((n) => n.y + 280));

    const countText = (o) => (!o ? '' : o.shape === 'group' ? `${o.count} 组` : String(o.count));
    const nodeEl = (n) => {
      const spec = cat.nodes[n.type];
      const inV = inOf(n.id, 0);
      const ptxt = paramText(cat, n, inV && inV.type, inV && inV.shape, templates, sets);
      const rows = [];
      for (let i = 0; i < nodeRows(cat, n); i++) {
        const ins = spec.ins[i]; const outs = spec.outs[i];
        const inShape = ins ? ((inOf(n.id, i) || {}).shape || (n.type === 'merge' ? 'group' : 'list')) : null;
        const inLabel = ins ? portLabel(inOf(n.id, i), ins) : null;
        const outLabel = outs ? portLabel(outOf(n.id, i), outs[0]) : null;
        rows.push(h('div', { key: i, className: 'nd-r' },
          ins ? h(React.Fragment, null, h('span', null, inLabel), h('i', { className: `pt l${inShape === 'group' ? ' sq' : ''}`, 'data-in': `${n.id}:${i}` })) : h('span'),
          outs ? h(React.Fragment, null, h('span', null, outLabel, h('b', null, countText(outOf(n.id, i)))),
            h('i', { className: `pt r${shapeOf(n.id, i) === 'group' ? ' sq' : ''}`, onPointerDown: (e) => startWire(e, n, i) })) : null));
      }
      const lines = [].concat(ptxt).filter((x) => x !== '');
      return h('div', { key: n.id, className: `nd${sel && sel.node === n.id ? ' sel' : ''}${errors[n.id] ? ' err' : ''}`, style: { left: n.x, top: n.y, width: NW },
        onPointerDown: (e) => { if (!e.target.classList.contains('pt')) startMove(e, n); } },
      h('div', { className: 'nd-h' }, spec.label), rows,
      lines.length ? h('div', { className: 'nd-p' }, lines.map((t, i) => h('div', { key: i }, t))) : null);
    };

    const wires = g.links.map((l, i) => {
      const a = byId[l.from[0]], b = byId[l.to[0]];
      if (!a || !b) return null;
      const d = wirePath(a.x + NW + 1, portY(a, l.from[1]), b.x - 1, portY(b, l.to[1]), a, b);
      return h('path', { key: i, d, className: `${shapeOf(a.id, l.from[1]) === 'group' ? 'g' : ''}${sel && sel.link === i ? ' sel' : ''}`,
        onPointerDown: (e) => { e.stopPropagation(); setSel({ link: i }); } });
    });
    if (drag) {
      const a = byId[drag.from[0]];
      wires.push(h('path', { key: 'drag', className: 'drag', d: wirePath(a.x + NW + 1, portY(a, drag.from[1]), drag.x, drag.y) }));
    }

    const saveCopy = () => send('POST', '/api/flows', { ...g, name: g.name + ' 副本', builtin: undefined })
      .then((n) => { location.hash = '#/flows/' + n.id; }).catch((e) => toast('error', e.message));
    const doRun = () => {
      setRunning(true);
      send('POST', `/api/flows/${g.id}/run`, g).then((r) => { setRun(r); setEv(r); reloadSets(); })
        .catch((e) => toast('error', e.message)).finally(() => setRunning(false));
    };

    const outputs = (run && run.outputs) || [];
    return h('div', { className: 'dm-row flowpage' },
      h('aside', { className: 'fl-pal' },
        ['来源', '处理', '输出'].map((c) => h(React.Fragment, { key: c },
          h('span', { className: 'fs-small fl-cat' }, c),
          Object.entries(cat.nodes).filter(([, v]) => v.cat === c).map(([k, v]) =>
            h('button', { key: k, type: 'button', className: 'pal', onClick: () => add(k) }, v.label))))),
      h('main', { className: 'fl-main' },
        h('div', { className: 'fl-bar' },
          h('div', { className: 'dm-meta', style: { flexGrow: 1 } }, run ? [
            h('span', { key: 't', className: 't' }, run.ran),
            h('span', { key: 'n' }, h('b', null, outputs.length), ' 项输出')] : null),
          g.builtin ? act('i-copy', '另存为流程', saveCopy) : null,
          h(E.Button, { variant: 'primary', size: 'sm', disabled: running, loading: running, onClick: doRun }, '运行流程')),
        h('div', { className: 'fl', ref: box, onPointerDown: (e) => {
          if (e.target !== box.current && !e.target.classList.contains('fl-in') && e.target.tagName !== 'svg') return;
          // dragging the empty canvas pans it (a touch screen has no other way to scroll it)
          const el = box.current, x0 = e.clientX, y0 = e.clientY, sl = el.scrollLeft, st = el.scrollTop;
          let moved = false;
          const move = (ev2) => {
            if (Math.abs(ev2.clientX - x0) + Math.abs(ev2.clientY - y0) > 4) moved = true;
            el.scrollLeft = sl - (ev2.clientX - x0); el.scrollTop = st - (ev2.clientY - y0);
          };
          const up = () => { removeEventListener('pointermove', move); removeEventListener('pointerup', up); if (!moved) setSel(null); };
          addEventListener('pointermove', move); addEventListener('pointerup', up);
        } },
          h('div', { className: 'fl-in', style: { width: W, height: H } },
            h('svg', { className: 'fl-w', width: W, height: H }, wires),
            g.nodes.map(nodeEl))),
        outputs.length ? h('section', { className: 'outs' },
          h('h2', { className: 'fs-lead', style: { margin: 0 } }, '输出'),
          outputs.map((o, i) => h('div', { key: i, className: 'out' },
            h('span', { className: 'fs-small', style: { fontFamily: 'var(--font-medium)', flexGrow: 1 } }, o.name),
            h('div', { className: 'dm-meta', style: { fontSize: 12 } }, o.meta.map((m, j) => h('span', { key: j }, m))),
            o.kind === 'set'
              ? act('i-arrow-r', '打开题组', () => { location.hash = '#/sets/' + o.set; })
              : act(o.kind === 'zip' ? 'i-box' : 'i-doc', o.kind === 'zip' ? '下载 ZIP' : '下载 PDF',
                () => download(`/api/flows/${g.id}/out/${o.file}?name=${encodeURIComponent(o.name)}`))))) : null),
      h('aside', { className: 'fl-insp' },
        sel && sel.link != null && g.links[sel.link]
          ? h(React.Fragment, null,
            h('div', { className: 'panel-row' },
              h('h2', { className: 'fs-lead panel-title' }, '连线'),
              act('i-trash', '删除连线', del)),
            h('div', { className: 'dm-meta' },
              h('span', null, cat.nodes[byId[g.links[sel.link].from[0]].type].label), h('span', null, '→'),
              h('span', null, cat.nodes[byId[g.links[sel.link].to[0]].type].label)))
          : sel && sel.node && byId[sel.node]
          ? h(Inspector, { cat, n: byId[sel.node], inV: inOf(sel.node, 0), in2: inOf(sel.node, 1), out: outOf(sel.node, 0),
            error: errors[sel.node], update, templates, sets, onDelete: del, outputs: outputs.filter((o) => o.node === sel.node) })
          : h(FlowProps, { g, setG, onDeleted: () => { location.hash = '#/templates/flows'; } , toast })));
  }

  function FlowProps({ g, setG, onDeleted, toast }) {
    const [deleting, setDeleting] = useState(false);
    return h(React.Fragment, null,
      h('div', { className: 'panel-row' },
        h('h2', { className: 'fs-lead panel-title' }, '流程'),
        g.builtin ? null : act('i-trash', '删除流程', () => setDeleting(true))),
      g.builtin ? h('p', { className: 'lock-note' }, '内置流程不可修改，另存为流程后可修改副本') : null,
      h(E.TextField, { label: '名称', size: 'sm', value: g.name, disabled: g.builtin, onChange: (e) => setG({ ...g, name: e.target.value }) }),
      deleting ? h(E.Dialog, { open: true, danger: true, title: '删除流程', confirmLabel: '删除流程', onClose: () => setDeleting(false),
        onConfirm: () => send('DELETE', '/api/flows/' + g.id).then(onDeleted).catch((e) => toast('error', e.message)) },
      h('p', null, `删除后 ${g.name} 将无法恢复。`)) : null);
  }

  function Inspector({ cat, n, inV, in2, out, error, update, templates, sets, onDelete, outputs }) {
    const spec = cat.nodes[n.type];
    const p = n.params || {};
    const t = (inV && inV.type) || 'q';
    const fields = (cat.fields[t] || []).map(([v, label]) => ({ value: v, label }));
    const sel = (label, value, options, onChange) => h(E.Select, { label, size: 'sm', value, options, onChange });
    let body = null;
    if (n.type === 'bank') body = sel('考试', p.exam || '9709', cat.exams.map((e) => ({ value: e, label: e })), (v) => update(n.id, { exam: v }));
    if (n.type === 'book') body = sel('教材', p.book || '9709_p1', cat.books.map((b) => ({ value: b.value, label: b.label })), (v) => update(n.id, { book: v }));
    if (n.type === 'set') body = sel('题组', p.set || '', sets.map((s) => ({ value: s.id, label: s.name })), (v) => update(n.id, { set: v }));
    if (n.type === 'filter') {
      const conds = p.conds || [];
      const put = (i, patch) => update(n.id, { conds: conds.map((c, j) => (j === i ? { ...c, ...patch } : c)) });
      body = h('div', { style: { display: 'flex', flexDirection: 'column', gap: 8 } },
        h('div', { className: 'panel-row' },
          h('span', { className: 'fs-small panel-title' }, '条件'),
          act('i-plus', '添加条件', () => update(n.id, { conds: conds.concat([{ field: fields[0] ? fields[0].value : 'year', op: '=', value: '' }]) }))),
        conds.map((c, i) => h('div', { key: i, className: 'cond' },
          h('div', { className: 'cond-f' }, h(E.Select, { ariaLabel: '字段', size: 'sm', value: c.field, options: fields, onChange: (v) => put(i, { field: v }) })),
          h('div', { className: 'cond-d' }, h(E.IconButton, { icon: 'i-close', label: '删除条件', variant: 'ghost', size: 'sm', onClick: () => update(n.id, { conds: conds.filter((_, j) => j !== i) }) })),
          h('div', { className: 'cond-o' }, h(E.Select, { ariaLabel: '运算符', size: 'sm', value: c.op, options: cat.ops.map((o) => ({ value: o, label: o })), onChange: (v) => put(i, { op: v }) })),
          h('div', { className: 'cond-v' }, h(E.TextField, { ariaLabel: '值', size: 'sm', value: String(c.value ?? ''), onChange: (e) => put(i, { value: e.target.value }) })))));
    }
    if (n.type === 'sort') {
      body = h(React.Fragment, null,
        h('fieldset', { className: 'opt-group ex' }, h('legend', null, '依据'),
          h(E.Radio, { name: 'by-' + n.id, checked: p.by !== 'random', onChange: () => update(n.id, { by: 'field' }) }, '字段'),
          h(E.Radio, { name: 'by-' + n.id, checked: p.by === 'random', onChange: () => update(n.id, { by: 'random', seed: p.seed ?? 1 }) }, '随机')),
        p.by === 'random'
          ? h(E.TextField, { label: '种子', size: 'sm', value: String(p.seed ?? 1), onChange: (e) => update(n.id, { seed: e.target.value }) })
          : h(React.Fragment, null,
            sel('字段', p.field || 'marks', fields, (v) => update(n.id, { field: v })),
            h(E.SegmentedControl, { ariaLabel: '顺序', value: p.desc ? 'desc' : 'asc', onChange: (v) => update(n.id, { desc: v === 'desc' }),
              options: [{ value: 'asc', label: '升序' }, { value: 'desc', label: '降序' }] })));
    }
    if (n.type === 'take') body = h(E.TextField, { label: '条数', size: 'sm', value: String(p.n ?? 10), onChange: (e) => update(n.id, { n: e.target.value }) });
    if (n.type === 'group') body = sel('字段', p.field || 'topic', fields, (v) => update(n.id, { field: v }));
    if (n.type === 'join') {
      const lt = (inV && inV.type) || 'c', rt = (in2 && in2.type) || 'q';
      body = h(React.Fragment, null,
        sel('左侧字段', p.left || 'topic', (cat.fields[lt] || []).map(([v, l]) => ({ value: v, label: l })), (v) => update(n.id, { left: v })),
        sel('右侧字段', p.right || 'topic', (cat.fields[rt] || []).map(([v, l]) => ({ value: v, label: l })), (v) => update(n.id, { right: v })));
    }
    if (n.type === 'export') body = sel('导出模板', p.template || 'default', templates.map((x) => ({ value: x.id, label: x.name })), (v) => update(n.id, { template: v }));
    if (n.type === 'newset') body = h(E.TextField, { label: '名称', size: 'sm', value: p.name || '', onChange: (e) => update(n.id, { name: e.target.value }) });

    const shown = out || (spec.outs.length ? null : inV);
    return h(React.Fragment, null,
      h('div', { className: 'panel-row' },
        h('h2', { className: 'fs-lead panel-title' }, spec.label),
        act('i-trash', '删除节点', onDelete)),
      body ? h('div', { style: { display: 'flex', flexDirection: 'column', gap: 'var(--sub)' } }, body) : null,
      error ? h('div', { className: 'fl-err fs-small' }, error) : null,
      shown ? h('div', { className: 'sum' },
        h('div', { className: 'dm-meta' }, shown.shape === 'group'
          ? [h('span', { key: 'a' }, h('b', null, shown.count), ' 组'), h('span', { key: 'b' }, h('b', null, shown.items), shown.type === 'q' ? ' 题' : ' 条')]
          : [h('span', { key: 'a' }, h('b', null, shown.count), shown.type === 'q' ? ' 题' : ' 条')].concat(shown.marks != null ? [h('span', { key: 'b' }, h('b', null, shown.marks), ' 分')] : [])),
        h('div', { className: 'res' }, shown.rows.map((r, i) => h(React.Fragment, { key: i }, h('span', null, r[0]), h('b', null, r[1] === '' ? '' : r[1]))))) : null,
      outputs.length ? h('div', { className: 'sum' }, outputs.map((o, i) => h('div', { key: i, className: 'dm-meta' }, h('span', null, o.name), o.meta.map((m, j) => h('span', { key: j }, m))))) : null);
  }

  function FlowListPage({ toast, acts }) {
    const [flows, setFlows] = useState(null);
    useEffect(() => { api('/api/flows').then(setFlows); }, []);
    const create = () => send('POST', '/api/flows', { name: '批量生成', nodes: [], links: [] })
      .then((n) => { location.hash = '#/flows/' + n.id; }).catch((e) => toast('error', e.message));
    return h('div', { className: 'dm-row tplpage' },
      h(TopActs, { el: acts }, act('i-plus', '新建流程', create)),
      h('aside', { className: 'tpl-list' },
        h(KindTabs, { value: 'flow' }),
        flows ? h(E.List, { variant: 'two-line', selectable: true, ariaLabel: '批量生成流程', value: undefined,
          onChange: (v) => { location.hash = '#/flows/' + v; },
          items: flows.map((x) => ({ value: x.id, icon: 'i-grid', title: x.name, subtitle: x.summary })) }) : h(E.Loading, null)),
      h('main', { className: 'setmain empty-main' }, h(E.EmptyState, { icon: 'i-grid', title: '没有打开的流程' })));
  }

  function KindTabs({ value }) {
    return h(E.Tabs, { variant: 'line', value, ariaLabel: '模板类型', items: [{ value: 'export', label: '导出' }, { value: 'flow', label: '批量生成' }],
      onChange: (v) => { location.hash = v === 'flow' ? '#/templates/flows' : '#/templates'; } });
  }

  function SettingsPage() {
    const [o, setO] = useState(null);
    useEffect(() => { api('/api/settings').then(setO); }, []);
    if (!o) return h('div', { className: 'dm-row' }, h(E.Loading, null));
    const put = (k, v) => send('PUT', '/api/settings', { [k]: v }).then((n) => { setO(n); if (k === 'theme') applyTheme(v); });
    const radios = (legend, key, opts) => h('fieldset', { className: 'opt-group ex' }, h('legend', null, legend),
      opts.map(([v, label]) => h(E.Radio, { key: v, name: key, checked: o[key] === v, onChange: () => put(key, v) }, label)));
    const box = (key, label) => h(E.Checkbox, { checked: o[key], onChange: () => put(key, !o[key]) }, label);
    return h('main', { className: 'settings' },
      h('section', null, h('h2', { className: 'fs-lead' }, '题目卷'),
        h('div', { className: 'settings-grid' },
          h('fieldset', { className: 'opt-group ex' }, h('legend', null, 'CIE 题目'),
            h(E.Radio, { name: 'cie', checked: !o.cie_space, onChange: () => put('cie_space', false) }, '仅题目'),
            h(E.Radio, { name: 'cie', checked: o.cie_space, onChange: () => put('cie_space', true) }, '含答题区')),
          radios('入学考选择题', 'adm_layout', [['two', '每页两题'], ['flow', '连续排列']]),
          h('fieldset', { className: 'opt-group ex' }, h('legend', null, '页脚'),
            box('footer_name', '题组名称'), box('footer_code', '试卷代码与题号'), box('footer_page', '页码')))),
      h('section', null, h('h2', { className: 'fs-lead' }, '外观'),
        radios('主题', 'theme', [['system', '跟随系统'], ['light', '浅色'], ['dark', '深色']])));
  }

  function applyTheme(t) {
    try { localStorage.setItem('dm-theme', t); } catch (e) {}
    const light = t === 'light' || (t === 'system' && matchMedia('(prefers-color-scheme: light)').matches);
    document.documentElement.setAttribute('data-theme', light ? 'light' : 'dark');
  }

  // ------------------------------------------------------------------ shell

  function App() {
    const hash = useHash();
    const toast = E.useToast();
    const [metas, setMetas] = useState(null);
    const [sets, setSets] = useState([]);
    const [search, setSearch] = useState('');
    // The top bar's search field reports only Enter; it searches as one types (after a
    // pause), and Escape or the chip beside the result count clears it.
    const searchBox = () => document.querySelector('.dm-col > .topbar .search input');
    const clearSearch = useCallback(() => { const el = searchBox(); if (el) el.value = ''; setSearch(''); }, []);
    const [templates, setTemplates] = useState([]);
    const [flowTitle, setFlowTitle] = useState('');
    const [acts, setActs] = useState(null);        // the top bar's action slot, for the pages' actions
    useEffect(() => { if (metas && window.dmBoot) dmBoot.ready(); }, [metas]);   // index.html's loader
    const reloadSets = useCallback(() => api('/api/sets').then(setSets), []);
    const reloadTemplates = useCallback(() => api('/api/templates').then(setTemplates), []);
    useEffect(() => { api('/api/meta').then(setMetas); reloadSets(); reloadTemplates(); api('/api/settings').then((o) => applyTheme(o.theme)); }, []);

    const PAGES = ['query', 'sets', 'templates', 'flows', 'settings'];
    const page = hash.split('/')[1] || 'query';
    // an address that names no page goes to the query page
    useEffect(() => { if (!PAGES.includes(page)) location.replace('#/query'); }, [page]);
    // The sidebar opens when the pointer rests on it (not when it passes over), and
    // closes when the pointer leaves or an entry is clicked; keyboard focus opens it too.
    const [navOpen, setNavOpen] = useState(false);
    const navTimer = useRef(0);
    const navEnter = () => { clearTimeout(navTimer.current); navTimer.current = setTimeout(() => setNavOpen(true), 120); };
    const navClose = () => { clearTimeout(navTimer.current); setNavOpen(false); };
    const navClick = (e) => {
      if (!e.target.closest('a, button')) return;
      navClose();
      if (document.activeElement) document.activeElement.blur();
    };
    const navFocus = (e) => { if (e.target.matches(':focus-visible')) setNavOpen(true); };
    const navBlur = (e) => { if (!e.currentTarget.contains(e.relatedTarget)) navClose(); };
    useEffect(() => {
      const el = searchBox();
      if (!el) return;
      el.value = search;
      let t = 0;
      const typed = () => { clearTimeout(t); t = setTimeout(() => setSearch(el.value.trim()), 250); };
      const key = (e) => { if (e.key === 'Escape') { clearTimeout(t); clearSearch(); } };
      el.addEventListener('input', typed);
      el.addEventListener('keydown', key);
      return () => { clearTimeout(t); el.removeEventListener('input', typed); el.removeEventListener('keydown', key); };
    }, [page, !!metas]);
    const nav = [
      { value: 'query', label: '查询', icon: 'i-search', href: '#/query' },
      { value: 'sets', label: '题组', icon: 'i-list', href: '#/sets' },
      { value: 'templates', label: '模板', icon: 'i-doc', href: '#/templates' },
    ];
    const titles = { query: '查询', sets: '题组', templates: '模板', settings: '设置' };
    const [, , arg, sub, subArg] = hash.split('/');
    const cur = page === 'sets' ? sets.find((x) => x.id === arg) : null;
    let body;
    if (!metas) body = null;
    else if (page === 'sets' && sub === 'paper') {
      body = cur ? h('div', { className: 'dm-row' }, h(PaperPage, { s: cur })) : h(E.Loading, null);
    } else if (page === 'sets' && sub === 'export') {
      body = cur && templates.length ? h(ExportPage, { key: cur.id, s: cur, tid: subArg, templates, reloadTemplates, toast, acts }) : h(E.Loading, null);
    } else if (page === 'sets') body = h(SetsPage, { sets, current: arg, reloadSets, templates, toast, acts });
    else if (page === 'templates' && arg === 'flows') body = h(FlowListPage, { toast, acts });
    else if (page === 'flows') body = templates.length ? h(FlowPage, { key: arg, fid: arg, templates, sets, reloadSets, toast, onTitle: setFlowTitle }) : h(E.Loading, null);
    else if (page === 'templates') {
      body = templates.length ? h(TemplatesPage, { templates, current: arg, reloadTemplates, sets, toast, acts }) : h(E.Loading, null);
    } else if (page === 'settings') body = h('div', { className: 'dm-row' }, h(SettingsPage));
    else if (page === 'query') body = h(QueryPage, { metas, search, clearSearch, sets, reloadSets, toast });
    else body = null;
    const title = sub === 'paper' ? '题目卷' : sub === 'export' ? '导出' : page === 'flows' ? (flowTitle || '批量生成') : (titles[page] || '查询');
    // the browser tab names the page and, on a set's pages, the set
    useEffect(() => {
      document.title = page === 'sets' && cur ? (sub ? `${cur.name} ${title}` : cur.name) : title;
    }, [page, sub, cur && cur.name, title]);
    return h('div', { className: 'dm-shell' },
      h('div', { className: 'dm-nav', 'data-tool': page === 'settings' ? 'settings' : undefined, onMouseEnter: navEnter, onMouseLeave: navClose, onClickCapture: navClick, onFocus: navFocus, onBlur: navBlur },
        h(E.Sidebar, { name: 'AL 题库', items: nav, value: page === 'flows' ? 'templates' : page, open: navOpen,
          tools: [{ label: '设置', icon: 'i-sliders', onClick: () => { location.hash = '#/settings'; } }] })),
      h('div', { className: 'dm-col' },
        h(E.TopBar, {
          title,
          crumbs: page === 'sets' && (sub === 'paper' || sub === 'export') && cur
            ? [{ label: '题组', href: '#/sets/' + arg }, { label: cur.name, href: '#/sets/' + arg }, { label: sub === 'paper' ? '题目卷' : '导出' }]
            : page === 'flows' ? [{ label: '模板', href: '#/templates' }, { label: '批量生成', href: '#/templates/flows' }] : undefined,
          search: page === 'query' ? '搜索' : undefined, onSearch: setSearch,
          actions: h('div', { ref: setActs, className: 'dm-acts' }) }),
        body));
  }

  ReactDOM.createRoot(document.getElementById('root')).render(h(E.ToastProvider, null, h(App)));
})();
