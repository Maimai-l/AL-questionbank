/* 题库数据管理 (docs/data-manager.md). React without a build step: h = createElement.
   Pages: #/query, #/search, #/sets/<id>[/board/<board>], #/templates/<id>, #/templates/flows[/<id>], #/flows/<id>, #/settings. */
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
  const SEASON = { 3: 'F/M', 6: 'M/J', 11: 'O/N' };
  // the task types of the parts (docs/ui-text.md 3.1)
  const TASK = { find: '求解', calculate: '计算', explain: '解释', prove: '证明', sketch: '草绘', draw: '作图',
    hypothesis_test: '检验', logic: '逻辑', write_code: '编程', complete_code: '补全', trace: '追踪', test: '测试',
    sql: 'SQL', assembly: '汇编', other: '其他' };

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
    const li = menu.closest('.li');            // a list item's menu: outside the list, level with the item
    const box = li && li.closest('.list').getBoundingClientRect();
    const left = li ? Math.min(box.right + 8, innerWidth - m.width - 8)
      : Math.max(8, Math.min(toRight ? r.right - m.width : r.left, innerWidth - m.width - 8));
    const top = li ? Math.max(8, Math.min(li.getBoundingClientRect().top, innerHeight - m.height - 8))
      : up ? r.top - 4 - m.height : r.bottom + 4;
    if (li) s.maxHeight = '320px';
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
  function MoreMenu({ label = '更多', items, tip = true }) {
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
    const shown = items.filter(Boolean);
    return h('div', { ref, className: 'dd more-dd', onClick: (e) => e.stopPropagation(), onKeyDown: (e) => e.stopPropagation() },
      h(E.IconButton, { icon: 'i-more', label, variant: 'ghost', size: 'sm', tooltip: open || !tip ? undefined : 'below',
        'aria-haspopup': 'menu', 'aria-expanded': open, onClick: () => setOpen(!open) }),
      h('div', { className: 'menu', role: 'menu', hidden: !open },
        shown.map((it, i) => h(React.Fragment, { key: it.label },
          it.danger && i ? h('div', { className: 'menu-sep', role: 'separator' }) : null,
          h('button', { type: 'button', role: 'menuitem', className: 'menu-item' + (it.danger ? ' is-danger' : ''),
            onClick: () => { setOpen(false); it.onClick(); } }, it.label)))));
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
      if (e.pointerType === 'mouse') {
        // focused for the arrow keys, but a click is not keyboard work: no focus ring until a key is pressed
        e.preventDefault(); body.current.dataset.pointer = '1'; e.currentTarget.focus();
      }
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
      delete body.current.dataset.pointer;
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
      return h('td', { key: c.key, className: c.kind === 'id' ? 'c-id' : c.kind === 'text' ? 'c-text' : undefined, title: c.kind === 'text' ? v : undefined }, v);
    };
    return h('div', { className: 'tbl-frame' },
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
    const what = topics.length && topics.length < allTopics.length ? topics.map((t) => t.label).join('、') : comps.join('、');
    const years = f.from === f.to ? String(f.from) : `${f.from}-${f.to}`;
    return [meta.exam, what, years].filter(Boolean).join(' ');
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
      h('div', { className: grid ? 'fx-grid' : null }, items.map((i) => h('div', { className: 'fx-row' + (i.zero ? ' is-zero' : ''), key: i.value },
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

  function QueryPage({ metas, sets, reloadSets, toast }) {
    const [exam, setExam] = useState('9709');
    // the search field above the table: it searches as one types (after a pause); Escape or
    // the clear button empties it
    const [text, setText] = useState('');
    const [search, setSearch] = useState('');
    useEffect(() => { const t = setTimeout(() => setSearch(text.trim()), 250); return () => clearTimeout(t); }, [text]);
    const clearSearch = () => { setText(''); setSearch(''); };
    const meta = metas.find((m) => m.exam === exam);
    const [rowsByExam, setRowsByExam] = useState({});
    const [f, setF] = useState(() => defaults(meta));
    const [hits, setHits] = useState(null);
    const [selected, setSelected] = useState([]);
    const [focus, setFocus] = useState(null);
    const [adding, setAdding] = useState(false);
    const allRows = rowsByExam[exam] || [];

    useEffect(() => {
      // the first list is drawn once the loader has finished (index.html, dmBoot.after)
      if (!rowsByExam[exam]) api('/api/questions?exam=' + exam).then((r) => afterBoot(() => setRowsByExam((o) => ({ ...o, [exam]: r }))));
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
        value: t, label: TASK[t] || t, n: n[t] || 0,
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
      .map((r) => ({ ...r, season: SEASON[r.month] || '', qn: 'Q' + r.q })), [rows]);

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
        h(Facet, { title: '试卷', items: compItems, picked: f.components, onChange: setComponents, grid: meta.components.length > 2 }),
        h('section', { style: { display: 'flex', flexDirection: 'column', gap: 'var(--el)' } },
          h('div', { className: 'fx-head' }, h('span', { className: 'fs-small', style: { fontFamily: 'var(--font-medium)' } }, '年份')),
          h('div', { className: 'years' },
            h(E.Select, { ariaLabel: '起始年份', size: 'sm', options: years, value: String(f.from), onChange: (v) => setF({ ...f, from: +v }) }),
            h('span', null, '至'),
            h(E.Select, { ariaLabel: '结束年份', size: 'sm', options: years, value: String(f.to), onChange: (v) => setF({ ...f, to: +v }) }))),
        topicItems.length ? h(Facet, { title: '主题', items: topicItems, picked: f.topics, onChange: (s) => setF({ ...f, topics: s }) }) : null,
        taskItems.length ? h(Facet, { title: '小问类型', items: taskItems, picked: tasks, onChange: (s) => setF({ ...f, tasks: s }) }) : null),
      h('main', { className: 'dm-results' },
        h('div', { className: 'headline' },
          h('span', null, `${view.length} 题`)),
        h('div', { className: 'selbar' },
          h('div', { className: 'q-search' },
            h(E.TextField, { 'aria-label': '搜索题目', placeholder: '搜索', icon: 'i-search', size: 'sm', value: text,
              onChange: (e) => setText(e.target.value), onKeyDown: (e) => { if (e.key === 'Escape') clearSearch(); } }),
            text ? h(E.IconButton, { icon: 'i-close', label: '清除搜索', variant: 'ghost', size: 'sm', onClick: clearSearch }) : null),
          h('div', { className: 'dm-meta', style: { flexGrow: 1, justifyContent: 'flex-end' } },
            h('span', null, '已选 ', h('b', null, picked.length), ' 题')),
          h(E.Button, { variant: 'primary', size: 'sm', icon: 'i-plus', disabled: !picked.length, onClick: () => setAdding(true) }, '加入题组')),
        h('div', { className: 'dm-tablebox' },
          allRows.length ? h(SelTable, {
            ariaLabel: '题目', rows: view, selected, onSelectedChange: setSelected, onActivate: setFocus, minWidth: 560,
            // a column whose value is the same in every row is left out (docs/ui-text.md 4.3)
            columns: [
              { key: 'year', label: '年份', kind: 'id', width: 96 },
              { key: 'season', label: '考季', kind: 'id', width: 72, sortValue: (r) => r.month },
              { key: 'paper', label: '卷号', kind: 'id', width: 64 },
              { key: 'qn', label: '题号', kind: 'id', width: 64, sortValue: (r) => r.q },
              { key: 'stem', label: '题干', kind: 'text', sortable: false },
            ].filter((c) => c.kind !== 'id' || c.key === 'qn' || view.length < 2 || view.some((r) => r[c.key] !== view[0][c.key])),
          }) : h(E.Loading, { label: '正在读取题目' }),
          allRows.length && !view.length ? h(E.EmptyState, { icon: 'i-search', title: '没有符合条件的题目' }) : null)),
      h(Detail, { qid: focus }),
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

  // ------------------------------------------------------------------ search page

  /** Marks every match of the patterns in the element's text, formulas left out. */
  function markWords(root, patterns) {
    const re = new RegExp(patterns.join('|'), 'gi');
    const walk = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, {
      acceptNode: (n) => (n.parentElement.closest('.katex, mark') ? NodeFilter.FILTER_REJECT : NodeFilter.FILTER_ACCEPT) });
    const nodes = [];
    while (walk.nextNode()) nodes.push(walk.currentNode);
    nodes.forEach((n) => {
      const t = n.nodeValue;
      re.lastIndex = 0;
      if (!re.test(t)) return;
      re.lastIndex = 0;
      const frag = document.createDocumentFragment();
      let at = 0, m;
      while ((m = re.exec(t))) {
        if (!m[0]) { re.lastIndex++; continue; }
        frag.appendChild(document.createTextNode(t.slice(at, m.index)));
        const k = document.createElement('mark'); k.textContent = m[0]; frag.appendChild(k);
        at = m.index + m[0].length;
      }
      frag.appendChild(document.createTextNode(t.slice(at)));
      n.parentNode.replaceChild(frag, n);
    });
  }

  /** A snippet from /api/find: \x01..\x02 around matches, formulas in $..$ drawn. */
  function Snippet({ text }) {
    const ref = useRef(null);
    useEffect(() => {
      const el = ref.current;
      if (!el) return;
      const esc = (x) => x.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
      // a mark inside a formula would break it: there the formula stays unmarked
      el.innerHTML = text.split(/((?<!\\)\$[^$]*\$)/).map((part, i) => (i % 2 ? esc(part.replace(/[\x01\x02]/g, ''))
        : esc(part).replace(/\x01/g, '<mark>').replace(/\x02/g, '</mark>'))).join('');
      if (window.renderMathInElement) window.renderMathInElement(el, { delimiters: [{ left: '$', right: '$', display: false }], throwOnError: false });
    }, [text]);
    return h('dd', { ref });
  }

  // The box's text and the four keyword fields are one query: the fields are read from
  // the text and, when edited, write it again.
  function queryTokens(text) {
    const out = [];
    const re = /"([^"]*)"?|(\S+)/g;
    let m;
    while ((m = re.exec(text))) {
      if (m[1] !== undefined) { if (m[1].trim()) out.push(['phrase', m[1].trim()]); }
      else if (m[2] === 'OR') out.push(['or']);
      else if (m[2].length > 1 && m[2][0] === '-') out.push(['not', m[2].slice(1)]);
      else out.push(['word', m[2]]);
    }
    return out;
  }
  function readQuery(text) {
    const f = { all: [], phrase: [], any: [], none: [] };
    const t = queryTokens(text);
    t.forEach((x, i) => {
      if (x[0] === 'or') return;
      const ored = (t[i - 1] && t[i - 1][0] === 'or') || (t[i + 1] && t[i + 1][0] === 'or');
      if (x[0] === 'not') f.none.push(x[1]);
      else if (ored) f.any.push(x[0] === 'phrase' ? `"${x[1]}"` : x[1]);
      else if (x[0] === 'phrase') f.phrase.push(x[1]);
      else f.all.push(x[1]);
    });
    return { all: f.all.join(' '), phrase: f.phrase.join(' '), any: f.any.join(' '), none: f.none.join(' ') };
  }
  function writeQuery(f) {
    const words = (s) => (s || '').trim().split(/\s+/).filter(Boolean);
    return [...words(f.all), f.phrase.trim() ? `"${f.phrase.trim().replace(/"/g, '')}"` : '',
      words(f.any).join(' OR '), ...words(f.none).map((w) => '-' + w.replace(/^-/, ''))].filter(Boolean).join(' ');
  }

  /** Several of many choices in a narrow column, the field as tall as the others: the chosen
      ones are pills inside it, by their short name (9709 1.1, the full name on hover); two
      fit, past two the first one and +n. The menu (the design system's .dd .menu) has the
      full names. */
  function MultiPick({ options, value, onChange, placeholder, short, ariaLabel }) {
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
    const label = (v) => (options.find((o) => o.value === v) || { label: v }).label;
    const flip = (v) => onChange(value.includes(v) ? value.filter((x) => x !== v) : value.concat([v]));
    const fit = value.length <= 2 ? 2 : 1;     // two pills fit the column's field; past two, one and +n
    const rest = value.length - fit;
    return h('div', { ref, className: 'dd mpick' },
      h('div', { className: 'input input--sm select' + (value.length ? ' has-pills' : ''), role: 'combobox', tabIndex: 0, 'aria-expanded': open, 'aria-label': ariaLabel,
        onClick: (e) => { if (!e.target.closest('.rm')) setOpen(!open); },
        onKeyDown: (e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); setOpen(!open); } } },
        value.length ? h('span', { className: 'pills' },
          value.slice(0, fit).map((v) => h('span', { key: v, className: 'tag tag--sm', title: label(v) }, short(v),
            h('button', { type: 'button', className: 'rm', 'aria-label': '移除 ' + label(v), onClick: () => flip(v) }, h(E.Icon, { name: 'i-close' })))),
          rest > 0 ? h('span', { className: 'tag tag--sm', title: value.slice(fit).map(label).join('\n') }, `+${rest}`) : null)
          : h('span', { className: 'val ph' }, placeholder),
        h(E.Icon, { name: 'i-tri-d', className: 'tri' })),
      h('div', { className: 'menu', role: 'listbox', 'aria-multiselectable': 'true', hidden: !open },
        options.map((o) => h('button', { key: o.value, type: 'button', className: 'menu-item', role: 'option',
          'aria-selected': value.includes(o.value), onClick: () => flip(o.value) }, o.label, h(E.Icon, { name: 'i-check', className: 'ok' })))));
  }

  const FIELDS_AT = [['stem', '题干'], ['ms', '评分细则'], ['ex', '详解'], ['topic', '主题名']];
  const FIELD_NAME = Object.fromEntries(FIELDS_AT);
  const RECENT = 'dm-search-recent';
  const recentList = () => { try { return JSON.parse(localStorage.getItem(RECENT)) || []; } catch (e) { return []; } };

  /** The search page (docs/data-manager.md, 搜索): every exam at once; the left column is
      the advanced search, the box above the results its keywords. */
  function SearchPage({ metas, sets, reloadSets, toast }) {
    const allExams = metas.map((m) => m.exam);
    const allYears = [...new Set(metas.flatMap((m) => m.years))].sort();
    const [text, setText] = useState('');
    const [q, setQ] = useState('');                       // the text searched (after a pause)
    const [exams, setExams] = useState(() => new Set(allExams));
    const [topics, setTopics] = useState([]);
    const [years, setYears] = useState([allYears[0], allYears[allYears.length - 1]]);
    const [cols, setCols] = useState(() => new Set(FIELDS_AT.map((x) => x[0])));
    const [more, setMore] = useState(false);
    const [comps, setComps] = useState(null);             // null: every paper
    const [tasks, setTasks] = useState(null);             // null: every task type
    const [expl, setExpl] = useState('any');
    const [sort, setSort] = useState('rel');
    const [res, setRes] = useState(null);
    const [busy, setBusy] = useState(false);
    const [selected, setSelected] = useState([]);
    const [focus, setFocus] = useState(null);
    const [adding, setAdding] = useState(false);
    const [recent, setRecent] = useState(recentList);

    useEffect(() => { const t = setTimeout(() => setQ(text.trim()), 250); return () => clearTimeout(t); }, [text]);
    const conds = { q, exams: [...exams], topics, from: years[0], to: years[1], cols: [...cols], comps, tasks, expl, sort };
    const key = JSON.stringify(conds);
    useEffect(() => {
      if (!q) { setRes(null); return undefined; }
      let live = true;
      setBusy(true);
      send('POST', '/api/find', conds).then((r) => { if (live) { setRes(r); setBusy(false); } })
        .catch((e) => { if (live) { setBusy(false); toast('error', e.message); } });
      return () => { live = false; };
    }, [key]);
    useEffect(() => { setSelected([]); }, [key]);
    useEffect(() => { setFocus(res && res.rows.length ? res.rows[0].id : null); }, [res]);

    // a search is kept in 最近搜索 when it is used: Enter, a result opened, 加入题组
    const want = useRef(null);
    const keep = (query, n) => {
      const list = [{ q: query, n }].concat(recentList().filter((x) => x.q !== query)).slice(0, 8);
      setRecent(list);
      try { localStorage.setItem(RECENT, JSON.stringify(list)); } catch (e) {}
    };
    const remember = () => {
      const now = text.trim();
      if (!now) return;
      if (res && q === now && !busy) keep(now, res.total); else want.current = now;
    };
    useEffect(() => { if (res && !busy && want.current === q) { want.current = null; keep(q, res.total); } }, [res, busy]);
    const kw = readQuery(text);
    const setKw = (k, v) => setText(writeQuery({ ...kw, [k]: v }));
    const toggle = (set, setter, v) => { const n = new Set(set); n.has(v) ? n.delete(v) : n.add(v); setter(n); };

    // the topics of the chosen exams; a topic stays chosen only while its exam is
    const topicOptions = metas.filter((m) => exams.has(m.exam)).flatMap((m) => {
      const seen = new Set();
      return m.topics.filter((t) => !seen.has(t.value) && seen.add(t.value))
        .map((t) => ({ value: `${m.exam}:${t.value}`, label: `${m.exam} · ${t.label}` }));
    });
    useEffect(() => { setTopics((ts) => ts.filter((t) => exams.has(t.split(':')[0]))); }, [[...exams].join()]);
    // the papers of the chosen exams; a number named differently by two exams takes the CIE name (Paper 1)
    const compNames = new Map();
    metas.filter((m) => exams.has(m.exam)).sort((a, b) => b.cie - a.cie)
      .forEach((m) => m.components.forEach((c) => { if (!compNames.has(c.value)) compNames.set(c.value, c.label); }));
    const compOptions = [...compNames.entries()]
      .sort((a, b) => String(a[0]).localeCompare(String(b[0]), undefined, { numeric: true }));
    const taskOptions = Object.keys((res && res.tasks) || {}).sort((a, b) => Object.keys(TASK).indexOf(a) - Object.keys(TASK).indexOf(b));
    const yearOpts = allYears.map((y) => ({ value: String(y), label: String(y) }));
    const counts = (res && res.counts) || {};
    const papers = (res && res.papers) || {};
    const rows = (res && res.rows) || [];
    const picked = rows.filter((r) => selected.includes(r.id));
    const moreSet = tasks !== null || expl !== 'any';

    const head = (t, extra) => h('div', { className: 'fx-head' }, h('span', { className: 'sec-t' }, t), extra || null);
    const field = (label, k) => h('div', { className: 'kw' }, h('label', null, label),
      h(E.TextField, { 'aria-label': label, size: 'sm', value: kw[k], onChange: (e) => setKw(k, e.target.value),
        onKeyDown: (e) => { if (e.key === 'Enter') remember(); } }));
    const allOn = exams.size === allExams.length;
    return h('div', { className: 'dm-row' },
      h('aside', { className: 'dm-cond sp-left', 'aria-label': '高级搜索' },
        h(Facet, { title: '考试', grid: true, picked: exams, onChange: setExams,
          items: allExams.map((e) => ({ value: e, label: e, n: res ? counts[e] || 0 : '', zero: res && !counts[e] })) }),
        h(Facet, { title: '试卷', grid: true, picked: new Set(comps || compOptions.map((c) => c[0])),
          onChange: (set) => setComps(set.size === compOptions.length ? null : [...set]),
          items: compOptions.map(([v, label]) => ({ value: v, label, n: res ? papers[v] || 0 : '', zero: res && !papers[v] })) }),
        h('section', { className: 'sec' }, head('主题'),
          h(MultiPick, { ariaLabel: '主题', placeholder: '全部主题', options: topicOptions, value: topics, onChange: setTopics,
            short: (v) => v.replace(':', ' ') })),
        h('section', { className: 'sec' }, head('年份'),
          h('div', { className: 'years' },
            h(E.Select, { ariaLabel: '起始年份', size: 'sm', options: yearOpts, value: String(years[0]), onChange: (v) => setYears([+v, Math.max(+v, years[1])]) }),
            h('span', null, '至'),
            h(E.Select, { ariaLabel: '结束年份', size: 'sm', options: yearOpts, value: String(years[1]), onChange: (v) => setYears([Math.min(+v, years[0]), +v]) }))),
        h('hr', { className: 'sp-hr' }),
        h('section', { className: 'sec' }, head('关键词'),
          field('包含全部词语', 'all'), field('包含完整短语', 'phrase'), field('包含任一词语', 'any'), field('不包含词语', 'none')),
        h('section', { className: 'sec' }, head('查找位置'),
          h('div', { className: 'fx-grid' }, FIELDS_AT.map(([k, label]) => h('div', { key: k, className: 'fx-row' }, h(E.Checkbox, { checked: cols.has(k),
            onChange: () => { if (!(cols.has(k) && cols.size === 1)) toggle(cols, setCols, k); } }, label))))),
        h('hr', { className: 'sp-hr' }),
        h('section', { className: 'sec' },
          h('button', { type: 'button', className: 'more-h', 'aria-expanded': more, onClick: () => setMore(!more) },
            h(E.Icon, { name: more ? 'i-chev-d' : 'i-chev-r', size: 'sm' }), h('span', null, '更多条件'),
            more ? null : h('span', { className: 'more-s' }, moreSet ? '已设置' : '不限')),
          more && taskOptions.length ? h(Facet, { title: '小问类型', grid: true, picked: new Set(tasks || taskOptions),
            onChange: (set) => setTasks(set.size === taskOptions.length ? null : [...set]),
            items: taskOptions.map((t) => ({ value: t, label: TASK[t] || t, n: res.tasks[t] })) }) : null,
          more ? h(E.Select, { label: '详解', size: 'sm', value: expl, onChange: setExpl,
            options: [{ value: 'any', label: '不限' }, { value: 'y', label: '有详解' }, { value: 'n', label: '无详解' }] }) : null)),
      h('main', { className: 'sp-main' },
        h('div', { className: 'sp-box' },
          h(E.TextField, { 'aria-label': '搜索', placeholder: '搜索', icon: 'i-search', value: text, onChange: (e) => setText(e.target.value),
            onKeyDown: (e) => { if (e.key === 'Escape') setText(''); if (e.key === 'Enter') remember(); } }),
          text ? h(E.IconButton, { icon: 'i-close', label: '清除搜索', variant: 'ghost', size: 'sm', onClick: () => setText('') }) : null),
        !q ? h('div', { className: 'sp-recent' },
          recent.length ? h('h3', null, '最近搜索') : null,
          recent.length ? recent.map((x) => h('button', { type: 'button', className: 'rec', key: x.q, onClick: () => setText(x.q) },
            h(E.Icon, { name: 'i-search', size: 'sm' }), h('span', null, x.q), h('span', null, `${x.n} 题`)))
            : h(E.EmptyState, { icon: 'i-search', title: '未搜索' }))
        : !res ? h(E.Loading, null)
        : h(React.Fragment, null,
          h('div', { className: 'headline' + (busy ? ' is-busy' : '') }, h('span', null, `${res.total} 题`)),
          h('div', { className: 'selbar' },
            h(E.Checkbox, { checked: rows.length > 0 && picked.length === rows.length, indeterminate: picked.length > 0 && picked.length < rows.length,
              onChange: () => setSelected(picked.length === rows.length ? [] : rows.map((r) => r.id)) }, '全选'),
            h(E.SegmentedControl, { ariaLabel: '排序', value: sort, onChange: setSort, options: [{ value: 'rel', label: '相关度' }, { value: 'year', label: '年份' }] }),
            h('div', { className: 'dm-meta', style: { flexGrow: 1, justifyContent: 'flex-end' } },
              h('span', null, '已选 ', h('b', null, picked.length), ' 题')),
            h(E.Button, { variant: 'primary', size: 'sm', icon: 'i-plus', disabled: !picked.length, onClick: () => { remember(); setAdding(true); } }, '加入题组')),
          rows.length ? h('div', { className: 'sp-list' },
            rows.map((r) => h('div', { key: r.id, className: 'hit' + (r.id === focus ? ' is-focus' : ''), onClick: (e) => { if (!e.target.closest('.check')) { setFocus(r.id); remember(); } } },
              h(E.Checkbox, { checked: selected.includes(r.id), ariaLabel: `选择 ${r.code} Q${r.q}`,
                onChange: () => setSelected(selected.includes(r.id) ? selected.filter((x) => x !== r.id) : selected.concat([r.id])) }),
              h('div', { className: 'hit-h' }, h('span', { className: 'hit-code' }, `${r.code} Q${r.q}`),
                r.topic ? h('span', { className: 'hit-meta' }, `${r.topic} ${r.topic_name}`) : null),
              r.snippets.length ? h('dl', { className: 'hit-s' }, r.snippets.map(([c, t]) => [
                h('dt', { key: c + 'k' }, FIELD_NAME[c]), h(Snippet, { key: c + 'v', text: t })])) : null)),
            res.total > rows.length ? h('p', { className: 'empty-note sp-more' }, `仅列出前 ${rows.length} 题`) : null)
            : h(E.EmptyState, { icon: 'i-search', title: '没有符合条件的题目' }))),
      h(Detail, { qid: focus, marks: res && res.terms }),
      adding ? h(AddDialog, {
        sets, toast, ids: picked.map((r) => r.id), name: q, source: 'query',
        onClose: () => setAdding(false), onDone: () => { setAdding(false); reloadSets(); },
      }) : null);
  }

  // ------------------------------------------------------------------ detail panel

  function Detail({ qid, marks }) {
    const [d, setD] = useState(null);
    const [tab, setTab] = useState('ms');
    const body = useRef(null);
    useEffect(() => { setD(null); setTab('ms'); if (qid) api('/api/question/' + qid).then(setD); }, [qid]);
    // the search page's words, marked in what the panel shows (after the formulas are drawn)
    useEffect(() => {
      if (!marks || !marks.length || !body.current) return undefined;
      const t = setTimeout(() => { if (body.current) markWords(body.current, marks); }, 50);
      return () => clearTimeout(t);
    }, [d, tab, marks && marks.join('|')]);
    if (!qid) return h('aside', { className: 'detail' },
      h('div', { className: 'detail-body' }, h(E.EmptyState, { icon: 'i-list', title: '未选择题目' })));
    if (!d) return h('aside', { className: 'detail' }, h('div', { className: 'detail-body' }, h(E.Loading, null)));
    const img = d.image;
    const hasEx = d.explanation && d.explanation.parts && d.explanation.parts.length;
    const tabs = [{ value: 'ms', label: d.scheme ? '评分细则' : '答案与解析' }, { value: 'text', label: '题干文字' },
      { value: 'ex', label: '详解', disabled: !hasEx }];
    return h('aside', { className: 'detail' },
      h('div', { className: 'detail-head' },
        h('div', { className: 'detail-title' },
          h('h2', null, h('span', null, d.code), h('span', null, 'Q' + d.q)),
          d.paper_pdf ? act('i-doc', '打开原卷', () => openTab(`/paper/${d.id}#page=${(d.pages[0] || 0) + 1}`)) : null),
        h('div', { className: 'tags' },
          d.topic ? h(E.Tag, { size: 'sm' }, `${d.topic} ${d.topic_name}`) : null,
          d.diagram ? h(E.Tag, { size: 'sm' }, '含图') : null)),
      h('div', { className: 'detail-media' },
        img ? h('div', { className: 'qimg' }, h('img', { src: img.src, alt: `第 ${d.q} 题题目截图` })) : null),
      h('div', { className: 'detail-tabs' },
        h(E.Tabs, { variant: 'line', items: tabs, value: tab, onChange: setTab, ariaLabel: '题目资料' })),
      h('div', { className: 'detail-body', ref: body },
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
      h('h4', null, p.label || '整题'),
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

  function SetsPage({ sets, current, reloadSets, templates, toast }) {
    const s = sets.find((x) => x.id === current) || sets[0];
    const fileRef = useRef(null);
    const [renameId, setRenameId] = useState(null);     // 重命名题组 from a list item's menu
    const [deleting, setDeleting] = useState(null);
    const importFile = (e) => {
      const file = e.target.files[0];
      e.target.value = '';
      if (!file) return;
      file.text().then((t) => {
        let doc;
        try { doc = JSON.parse(t); } catch (err) { throw new Error('文件无法读取'); }
        return send('POST', '/api/sets/import', doc);
      })
        .then((n) => {
          toast(n.unknown && n.unknown.length ? 'warning' : 'success',
            n.unknown && n.unknown.length ? `${n.count} 题已导入，${n.unknown.length} 个编号不在题库中` : `${n.count} 题已导入`);
          reloadSets(); location.hash = '#/sets/' + n.id;
        })
        .catch((err) => toast('error', err.message || '文件无法读取'));
    };
    const create = () => send('POST', '/api/sets', { name: '未命名题组', items: [] })
      .then((n) => { nameNext = n.id; reloadSets(); location.hash = '#/sets/' + n.id; });
    return h('div', { className: 'dm-row' },
      h('aside', { className: 'setlist' },
        h('input', { ref: fileRef, type: 'file', accept: '.json,application/json', className: 'hidden-input', onChange: importFile }),
        h('div', { className: 'setlist-acts' },
          h(E.Button, { variant: 'secondary', size: 'sm', icon: 'i-plus', onClick: create }, '新建题组'),
          h(E.Button, { variant: 'secondary', size: 'sm', icon: 'i-upload', onClick: () => fileRef.current.click() }, '导入 JSON')),
        sets.length ? h(E.List, {
          variant: 'two-line', selectable: true, ariaLabel: '题组', value: s ? s.id : undefined,
          onChange: (v) => { location.hash = '#/sets/' + v; },
          items: sets.map((x) => ({ value: x.id, icon: SOURCE_ICON[x.source] || 'i-list', title: x.name, subtitle: `${x.count} 题`,
            trailing: h(MoreMenu, { label: '更多操作', tip: false, items: [
              { label: '重命名', onClick: () => { setRenameId(x.id); location.hash = '#/sets/' + x.id; } },
              { label: '复制题组', onClick: () => send('POST', '/api/sets', { name: x.name + ' 副本', items: x.items, source: x.source })
                .then((n) => { reloadSets(); location.hash = '#/sets/' + n.id; }).catch((e) => toast('error', e.message)) },
              { label: '删除题组', danger: true, onClick: () => setDeleting(x) }] }) })),
        }) : h(E.EmptyState, { icon: 'i-list', title: '没有题组' })),
      s ? h(SetDetail, { key: s.id, s, reloadSets, templates, toast, rename: renameId === s.id, onRename: () => setRenameId(null) })
        : h('main', { className: 'setmain' }),
      deleting ? h(E.Dialog, { open: true, danger: true, title: '删除题组', confirmLabel: '删除题组', onClose: () => setDeleting(null),
        onConfirm: () => send('DELETE', '/api/sets/' + deleting.id).then(() => {
          setDeleting(null); if (s && s.id === deleting.id) location.hash = '#/sets'; reloadSets();
        }).catch((e) => toast('error', e.message)) },
      h('p', null, `删除后 ${deleting.name} 将无法恢复。题库中的题目不受影响。`)) : null);
  }

  /** A set: a header with its name, how far the work has got and the two actions; the
      practice paper in the middle; its questions on the right. 「打开白板」 is the main
      action until the board has ink, then 「输出」 is. */
  function SetDetail({ s, reloadSets, templates, toast, rename, onRename }) {
    const [rows, setRows] = useState(null);
    const [selected, setSelected] = useState([]);
    const [renaming, setRenaming] = useState(() => nameNext === s.id);
    const [editing, setEditing] = useState(false);
    const [output, setOutput] = useState(false);
    const [boards, setBoards] = useState(null);
    const [pages, setPages] = useState(null);
    useEffect(() => { if (nameNext === s.id) nameNext = null; }, []);
    useEffect(() => { if (rename) { setRenaming(true); onRename(); } }, [rename]);

    useEffect(() => {
      const exams = [...new Set(s.items.map((q) => (/^\d{4}_/.test(q) ? q.slice(0, 4) : q.split('-')[0])))];
      Promise.all(exams.map((e) => api('/api/questions?exam=' + e))).then((lists) => {
        const by = {};
        lists.flat().forEach((r) => { by[r.id] = r; });
        setRows(by);
      });
    }, [s.id]);
    useEffect(() => {
      setPages(null);
      if (s.count) api(`/api/sets/${s.id}/paper`).then((p) => setPages(p.pages)).catch(() => setPages(0));
    }, [s.id, s.items.join(), s.name]);
    useEffect(() => { api(`/api/sets/${s.id}/boards`).then(setBoards).catch(() => setBoards(null)); }, [s.id, s.items.join()]);

    const items = s.items.filter((q) => rows && rows[q]);
    const view = items.map((q, i) => {
      const r = rows[q];
      return { ...r, n: String(i + 1).padStart(2, '0'), season: SEASON[r.month] || '', qn: 'Q' + r.q };
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
    const openBoard = () => send('POST', `/api/sets/${s.id}/board`).then((b) => { location.hash = `#/sets/${s.id}/board/${b.id}`; })
      .catch((e) => toast('error', e.message));
    const written = boards && boards.boards.find((b) => b.strokes > 0);
    const ready = s.count > 0 && pages != null;

    return h('div', { className: 'sd' },
      h('header', { className: 'sd-head' },
        h('div', { className: 'page-head' },
          h(EditableTitle, { value: s.name, editing: renaming, setEditing: setRenaming, label: '重命名题组', onSave: (name) => save({ name }) }),
          h('div', { className: 'dm-meta' },
            h('span', null, h('b', null, s.count), ' 题'),
            boards ? h('span', null, written ? `已作答，最后书写 ${written.updated}` : '未作答') : null)),
        h('div', { className: 'sd-acts' },
          h(E.Button, { variant: written ? 'secondary' : 'primary', size: 'md', disabled: !ready, onClick: openBoard }, '打开白板'),
          h(E.Button, { variant: written ? 'primary' : 'secondary', size: 'md', icon: 'i-box', disabled: !s.count || !templates.length, onClick: () => setOutput(true) }, '输出'),
          h(MoreMenu, { label: '更多操作', items: [
            { label: '打开评分细则', onClick: () => openTab(`/doc/${s.id}/scheme`) },
            s.docs.explanation ? { label: '打开详解', onClick: () => openTab(`/doc/${s.id}/explanation`) } : null,
            { label: '导出 JSON', onClick: () => download(`/api/sets/${s.id}/export`) }] }))),
      !s.count ? h('div', { className: 'sd-empty' }, h(E.EmptyState, { icon: 'i-list', title: '题组中没有题目' }))
        : h('div', { className: 'sd-body' },
          editing
            ? h('main', { className: 'sd-edit' },
              h('div', { className: 'dm-toolbar' },
                h('span', { className: 'dm-meta dm-grow' }, h('span', null, `已选 ${selected.length} 题`)),
                act('k-up', '上移题目', () => move(-1), { disabled: !selected.length }),
                act('k-down', '下移题目', () => move(1), { disabled: !selected.length }),
                act('i-trash', '移出题组', remove, { disabled: !selected.length }),
                h(E.Button, { variant: 'secondary', size: 'sm', onClick: () => { setEditing(false); setSelected([]); } }, '完成编辑')),
              h('div', { className: 'dm-tablebox' }, !rows ? h(E.Loading, null) : h(SelTable, {
                ariaLabel: '题组中的题目', rows: view, selected, onSelectedChange: setSelected, minWidth: 440,
                columns: [
                  { key: 'n', label: '序号', kind: 'id', width: 80 },
                  { key: 'year', label: '年份', kind: 'id', width: 72, sortable: false },
                  { key: 'season', label: '考季', kind: 'id', width: 72, sortable: false },
                  { key: 'paper', label: '卷号', kind: 'id', width: 64, sortable: false },
                  { key: 'qn', label: '题号', kind: 'id', sortable: false },
                ],
              })))
            : h('main', { className: 'sd-paper' }, pages == null ? h(E.Loading, { label: '正在生成练习卷' })
              : h('div', { className: 'sd-sheets' }, Array.from({ length: pages }, (_, n) =>
                h('img', { key: n + '-' + s.items.join(), className: 'sheet', loading: 'lazy', src: `/api/sets/${s.id}/paper/${n}.png`, alt: `第 ${n + 1} 页` })))),
          editing ? null : h('aside', { className: 'sd-qs' },
            h('div', { className: 'panel-row' },
              h('h2', { className: 'fs-lead panel-title' }, '题目'),
              h(E.Button, { variant: 'secondary', size: 'sm', onClick: () => { setEditing(true); setSelected([]); } }, '编辑')),
            h('ol', { className: 'sd-qlist' }, view.map((r) => h('li', { key: r.id },
              h('span', { className: 'n' }, r.n), h('span', { className: 'c' }, `${r.code} Q${r.q}`)))))),
      output ? h(OutputDialog, { s, templates, written: !!written, toast, onClose: () => setOutput(false) }) : null);
  }


  // in the window (manage.py window) there are no tabs: the system browser opens the page,
  // and the clipboard is the window's when the page's own is refused
  const bridge = () => window.pywebview && window.pywebview.api;
  const openTab = (path) => (bridge() ? bridge().open(path) : open(path, '_blank'));
  const copyText = (text) => (navigator.clipboard ? navigator.clipboard.writeText(text) : Promise.reject())
    .catch(() => (bridge() ? bridge().copy(text) : Promise.reject()));
  const download = (url) => { const a = document.createElement('a'); a.href = url; a.download = ''; document.body.appendChild(a); a.click(); a.remove(); };

  /** POST, then save the file the server sends. Resolves true when it was saved. */
  const fetchFile = (url, body, toast) => fetch(url, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) })
    .then((r) => {
      if (!r.ok) return r.text().then((t) => { throw new Error(t || r.statusText); });
      return Promise.all([r.blob(), r.headers.get('Content-Disposition') || '']);
    })
    .then(([b, disp]) => {
      const m = disp.match(/filename\*=UTF-8''([^;]+)/);
      const a = document.createElement('a');
      a.href = URL.createObjectURL(b);
      a.download = m ? decodeURIComponent(m[1]) : '';
      document.body.appendChild(a); a.click(); a.remove();
      setTimeout(() => URL.revokeObjectURL(a.href), 1000);
      return true;
    })
    .catch((e) => { toast('error', e.message); return false; });

  // what each kind of file in the output is called in the dialog's list
  const FILE_KIND = { 'question.png': '题目截图', 'question.md': '题干文字', 'mark_scheme.md': '评分细则', 'explanation.md': '详解' };

  /** The files of an output, grouped: a folder of page images is one line, the same file
      in every question's folder is one line, other files are a line each. */
  function fileGroups(files) {
    const groups = [];
    const at = {};
    files.forEach((f) => {
      const parts = f.path.split('/');
      const per = parts.length === 2 && /^\d/.test(parts[0]);
      const key = parts.length === 1 ? f.path : per ? 'q:' + parts[1] : 'd:' + parts[0];
      if (!(key in at)) {
        at[key] = groups.length;
        groups.push({ name: parts.length === 1 ? f.path : per ? (FILE_KIND[parts[1]] || parts[1]) : parts[0], n: 0, size: 0, images: !per && parts.length > 1 });
      }
      const g = groups[at[key]];
      g.n += 1; g.size += f.size;
    });
    return groups;
  }

  /** 输出: a template (the presets), adjusted for this once if needed, and the files it makes. */
  function OutputDialog({ s, templates, written, toast, onClose }) {
    const [space, setSpace] = useState(null);           // 版面 for this output; first the settings page's default
    useEffect(() => { api('/api/settings').then((o) => setSpace((v) => (v == null ? o.space : v))); }, []);
    const start = written ? '3-model' : '1-paper';
    const [tid, setTid] = useState(templates.some((t) => t.id === start) ? start : templates[0].id);
    const t = templates.find((x) => x.id === tid) || templates[0];
    const [st, setSt] = useState(t.settings);
    const [tuning, setTuning] = useState(false);
    const [busy, setBusy] = useState(false);
    useEffect(() => { setSt(t.settings); }, [tid]);
    const body = { settings: st, body: t.body, space };
    const pv = usePreview(s, st, t.body, space);

    const IMG = ['image', 'image_with_space', 'text'];
    const has = {
      q: st.documents.includes('question_paper') || st.per_question.some((k) => IMG.includes(k)),
      ms: st.per_question.includes('mark_scheme'),
      ex: st.per_question.includes('explanation'),
      ink: st.answers === 'written_pdf',
    };
    const pdf = st.format === 'pdf';
    const images = st.format === 'images';
    // the practice paper is in this output: 版面 applies
    const laidOut = pdf ? st.answers !== 'written_pdf' : st.documents.includes('question_paper');
    const toggle = (k) => {
      const on = !has[k];
      if (!on && ((k === 'q' && !has.ink) || (k === 'ink' && !has.q))) return;   // something must show the questions
      const per = st.per_question.filter((x) => x !== { ms: 'mark_scheme', ex: 'explanation' }[k]);
      if (k === 'q') setSt({ ...st, documents: on ? st.documents.concat('question_paper') : st.documents.filter((x) => x !== 'question_paper'),
        per_question: on ? st.per_question : st.per_question.filter((x) => !IMG.includes(x)) });
      else if (k === 'ink') setSt({ ...st, answers: on ? 'written_pdf' : 'none', answer_filename: '批注版' });
      else setSt({ ...st, per_question: on ? per.concat({ ms: 'mark_scheme', ex: 'explanation' }[k]) : per });
    };
    const box = (k, label, disabled) => h(E.Checkbox, { checked: has[k], disabled, onChange: () => toggle(k) }, label);
    const go = () => {
      setBusy(true);
      fetchFile(`/api/sets/${s.id}/output`, body, toast).then((ok) => { setBusy(false); if (ok) onClose(); });
    };
    const groups = pv ? fileGroups(pv.files) : [];
    // its own footer: the design system's confirm button closes the dialog at once, and the
    // dialog has to stay open while the file is made
    const footer = h(React.Fragment, null,
      h(E.Button, { variant: 'secondary', size: 'sm', onClick: onClose }, '取消'),
      h(E.Button, { variant: 'primary', size: 'sm', disabled: busy || !pv, loading: busy, onClick: go }, pdf ? '下载 PDF' : '下载 ZIP'));
    return h(E.Dialog, { open: true, title: '输出', onClose: busy ? () => {} : onClose, footer },
      h('div', { className: 'op' },
        h(E.Select, { label: '模板', value: tid, onChange: setTid, options: templates.map((x) => ({ value: x.id, label: x.name })) }),
        laidOut && space != null ? h(SpaceSlider, { value: space, onChange: setSpace }) : null,
        tuning ? h('div', { className: 'op-tune' },
          h('fieldset', { className: 'opt-group ex' }, h('legend', null, '格式'),
            h(E.SegmentedControl, { ariaLabel: '格式', value: pdf ? 'pdf' : 'zip', onChange: (v) => setSt({ ...st, format: v }), options: FORMATS })),
          h('fieldset', { className: 'opt-group ex' }, h('legend', null, pdf ? 'PDF 内容' : '压缩包包含'),
            h('div', { className: 'op-checks' },
              box('q', '题目', pdf), box('ms', '评分细则', pdf), box('ex', '详解', pdf || !s.docs.explanation), box('ink', '批注版', !written),
              pdf ? null : h(E.Checkbox, { checked: images, onChange: () => setSt({ ...st, format: images ? 'zip' : 'images' }) }, 'PDF 按页拆成图片'))))
          : h('div', null, h(E.Button, { variant: 'secondary', size: 'sm', icon: 'i-sliders', onClick: () => setTuning(true) }, '调整格式与内容')),
        h('div', { className: 'op-files' },
          h('h4', null, pdf ? '文件' : '压缩包内容'),
          !pv ? h(E.Loading, null) : pv.error ? h('span', { className: 'fl-err' }, pv.error) : groups.map((g) => h('div', { key: g.name, className: 'op-file' },
            h(E.Icon, { name: 'i-doc', size: 'sm' }), h('span', { className: 'op-name' }, g.name),
            h('span', { className: 'op-n' }, g.n > 1 ? `${g.n} 个文件` : ''),
            h('span', { className: 'op-n' }, sizeText(g.size)))),
          busy ? h(E.Progress, { label: pdf ? '正在生成 PDF' : '正在生成压缩包', valueText: pv ? `${pv.files.length} 个文件` : '', style: { width: '100%', marginTop: 'var(--sub)' } }) : null)));
  }

  /** The board inside the page: the whiteboard's writing page in a rounded frame, as it is.
      It reports the question and page in view; 「完成」 goes back to the set. */
  function BoardPage({ s, bid, acts }) {
    const [at, setAt] = useState(null);
    useEffect(() => {
      const on = (e) => { if (e.origin === location.origin && e.data && e.data.type === 'wb-page') setAt(e.data); };
      addEventListener('message', on);
      return () => removeEventListener('message', on);
    }, []);
    return h('div', { className: 'dm-row board-page' },
      h(TopActs, { el: acts },
        at ? h('span', { className: 'dm-meta board-at' }, at.label ? h('span', null, at.label) : null,
          h('span', null, '第 ', h('b', null, at.page), ' / ', h('b', null, at.pages), ' 页')) : null,
        h(E.Button, { variant: 'primary', size: 'md', onClick: () => { location.hash = '#/sets/' + s.id; } }, '完成')),
      h('div', { className: 'board-frame' }, h('iframe', { title: '白板', src: `/write/${encodeURIComponent(bid)}?embed=1` })));
  }

  // ------------------------------------------------------------------ export (F7) and templates (F8)

  const IMG = ['image', 'image_with_space'];
  const optsOf = (st) => {
    const per = st.per_question;
    return {
      image: per.some((k) => IMG.includes(k)), text: per.includes('text'), space: per.includes('image_with_space'),
      ms: per.includes('mark_scheme'), ex: per.includes('explanation'), paper: st.documents.includes('question_paper'),
      answers: st.answers === 'written_pdf', layout: st.layout, readme: !!st.prompt_file,
    };
  };
  const settingsOf = (st, o) => {
    const per = [];
    if (o.image) per.push(o.space ? 'image_with_space' : 'image');
    if (o.text) per.push('text');
    if (o.ms) per.push('mark_scheme');
    if (o.ex) per.push('explanation');
    const docs = st.documents.filter((d) => d !== 'question_paper').concat(o.paper ? ['question_paper'] : []);
    return { ...st, per_question: per, documents: docs, answers: o.answers ? 'written_pdf' : 'none', layout: o.layout,
      prompt_file: o.readme ? (st.prompt_file || 'README.md') : '' };
  };
  const sizeText = (n) => (n >= 1048576 ? (n / 1048576).toFixed(1) + ' MB' : Math.max(1, Math.round(n / 1024)) + ' KB');

  const FORMATS = [{ value: 'pdf', label: 'PDF' }, { value: 'zip', label: 'ZIP' }];

  /** The export options (docs/ui-text.md 2.3): the format, then for a PDF which one, for a
      ZIP what each question and the ZIP hold and how the files are laid out. */
  function ExportOptions({ settings, onChange }) {
    const o = optsOf(settings);
    const set = (k, v) => onChange(settingsOf(settings, { ...o, [k]: v }));
    // something must show the questions: the last of these cannot be turned off
    const QS = ['image', 'text', 'paper', 'answers'];
    const last = (k) => o[k] && QS.filter((x) => o[x]).length === 1;
    const box = (k, label, disabled) => h(E.Checkbox, { checked: o[k], disabled, onChange: () => { if (!last(k)) set(k, !o[k]); } }, label);
    const seg = (legend, value, options, onSeg) => h('fieldset', { className: 'opt-group ex' }, h('legend', null, legend),
      h(E.SegmentedControl, { ariaLabel: legend, value, onChange: onSeg, options }));
    const format = settings.format || 'zip';
    const images = format === 'images';
    return h(React.Fragment, null,
      seg('格式', format === 'pdf' ? 'pdf' : 'zip', FORMATS, (v) => onChange({ ...settings, format: v })),
      format === 'pdf'
        ? seg('PDF 内容', o.answers ? 'answers' : 'paper', [{ value: 'paper', label: '练习卷' }, { value: 'answers', label: '批注版' }],
          (v) => onChange(settingsOf(settings, { ...o, answers: v === 'answers', paper: true })))
        : h(React.Fragment, null,
          h('fieldset', { className: 'opt-group ex' }, h('legend', null, '每道题包含'),
            box('image', '题目截图'), h('div', { className: 'opt-sub' }, box('space', '截图保留原卷答题区', !o.image)), box('text', '题干文字'),
            box('ms', '评分细则'), box('ex', '详解')),
          h('fieldset', { className: 'opt-group ex' }, h('legend', null, '压缩包包含'),
            box('paper', '练习卷'), box('answers', '批注版'),
            h('div', { className: 'opt-sub' }, h(E.Checkbox, { checked: images, disabled: !o.paper && !o.answers,
              onChange: () => onChange({ ...settings, format: images ? 'zip' : 'images' }) }, 'PDF 按页拆成图片')),
            box('readme', 'README.md')),
          seg('文件结构', o.layout, [{ value: 'folder_per_question', label: '按题分文件夹' }, { value: 'flat', label: '不分文件夹' }],
            (v) => set('layout', v))));
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

  function usePreview(s, st, body, space) {
    const [pv, setPv] = useState(null);
    useEffect(() => {
      if (!s || !st) return undefined;
      const t = setTimeout(() => send('POST', `/api/sets/${s.id}/zip/preview`, { settings: st, body, space }).then(setPv)
        .catch((e) => setPv({ error: e.message, files: [], size: 0, readme: '', manifest: '' })), 200);
      return () => clearTimeout(t);
    }, [s && s.id, s && s.items.join(), JSON.stringify(st), body, space]);
    return pv;
  }

  const HOLES = [
    ['{title}', '题组名称'], ['{count}', '题数'], ['{total_marks}', '总分'], ['{papers}', '试卷'],
    ['{date}', '日期'], ['{question_table}', '题目表'], ['{file_tree}', '目录'],
  ];

  function TemplatesPage({ templates, current, reloadTemplates, sets, toast }) {
    const t = templates.find((x) => x.id === current) || templates[0];
    const [name, setName] = useState('');
    const [st, setSt] = useState(null);
    const [body, setBody] = useState('');
    const [tab, setTab] = useState('src');
    const firstSet = () => (sets.find((x) => x.count) || sets[0] || {}).id || '';
    const [sid, setSid] = useState(firstSet);
    const [deleting, setDeleting] = useState(null);
    const [renaming, setRenaming] = useState(false);
    const [renameId, setRenameId] = useState(null);     // 重命名模板 from a list item's menu
    const area = useRef(null);
    useEffect(() => { if (t && renameId === t.id) { setRenaming(true); setRenameId(null); } }, [renameId, t && t.id]);
    useEffect(() => { if (t) { setName(t.name); setSt(t.settings); setBody(t.body); } }, [t && t.id, templates.length]);
    // changes are saved as they are made (built-in templates are read-only); a change still
    // waiting is saved at once when another template is opened or the page is left
    const pending = useRef(null);
    useEffect(() => {
      if (!t || t.builtin || !st) return undefined;
      if (name === t.name && body === t.body && JSON.stringify(st) === JSON.stringify(t.settings)) return undefined;
      const id = t.id, data = { name, settings: st, body };
      const save = () => { clearTimeout(tm); pending.current = null; send('PUT', '/api/templates/' + id, data).then(() => reloadTemplates()).catch((e) => toast('error', e.message)); };
      const tm = setTimeout(save, 600);
      pending.current = save;
      return () => { clearTimeout(tm); };
    }, [name, body, JSON.stringify(st)]);
    useEffect(() => () => { if (pending.current) pending.current(); }, [t && t.id]);
    useEffect(() => { if (!sid) setSid(firstSet()); }, [sets.length]);
    const pv = usePreview(tab === 'preview' ? sets.find((x) => x.id === sid) : null, st, body);
    if (!t || !st) return h('div', { className: 'dm-row' }, h(E.Loading, null));
    const go = (id) => { location.hash = '#/templates/' + id; };
    const create = () => send('POST', '/api/templates', { name: '未命名模板', settings: templates[0].settings, body: templates[0].body })
      .then((n) => reloadTemplates().then(() => go(n.id)));
    const copy = (x) => send('POST', '/api/templates', { name: x.name + ' 副本', settings: x.settings, body: x.body })
      .then((n) => reloadTemplates().then(() => go(n.id))).catch((e) => toast('error', e.message));
    const insert = (v) => {
      const el = area.current;
      const a = el ? el.selectionStart : body.length;
      const b = el ? el.selectionEnd : body.length;
      setBody(body.slice(0, a) + v + body.slice(b));
      requestAnimationFrame(() => { if (el) { el.focus(); el.selectionStart = el.selectionEnd = a + v.length; } });
    };
    return h('div', { className: 'dm-row tplpage' },
      h('aside', { className: 'tpl-list' },
        h(KindTabs, { value: 'export' }),
        h('div', { className: 'setlist-acts' }, h(E.Button, { variant: 'secondary', size: 'sm', icon: 'i-plus', onClick: create }, '新建模板')),
        h(E.List, { variant: 'compact', selectable: true, ariaLabel: '导出模板', value: t.id, onChange: go,
          items: templates.map((x) => ({ value: x.id, title: x.name,
            trailing: h(MoreMenu, { label: '更多操作', tip: false, items: [
              x.builtin ? null : { label: '重命名', onClick: () => { setRenameId(x.id); go(x.id); } },
              { label: '复制模板', onClick: () => copy(x) },
              x.builtin ? null : { label: '删除模板', danger: true, onClick: () => setDeleting(x) }] }) })) })),
      h('section', { className: 'tpl-opts' },
        h('div', { className: 'title-line' },
          h(EditableTitle, { value: name, small: true, readOnly: t.builtin, editing: renaming, setEditing: setRenaming, label: '重命名模板', onSave: setName })),
        t.builtin ? h('p', { className: 'lock-note' }, '内置模板不可修改，复制模板后可修改副本') : null,
        h('div', { className: t.builtin ? 'opts locked' : 'opts' }, h(ExportOptions, { settings: st, onChange: t.builtin ? () => {} : setSt }))),
      st.format === 'pdf' ? h('section', { className: 'tpl-edit' }, h(E.EmptyState, { icon: 'i-doc', title: '没有 README' })) : h('section', { className: 'tpl-edit' },
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
          : h('div', { className: 'ex-docbody' }, pv && pv.error ? h(E.EmptyState, { icon: 'i-doc', title: pv.error }) : pv ? h(MdView, { text: pv.readme }) : sets.length ? h(E.Loading, null) : h(E.EmptyState, { icon: 'i-list', title: '没有题组' }))),
      deleting ? h(E.Dialog, { open: true, danger: true, title: '删除模板', confirmLabel: '删除模板', onClose: () => setDeleting(null),
        onConfirm: () => send('DELETE', '/api/templates/' + deleting.id).then(() => reloadTemplates())
          .then(() => { if (deleting.id === t.id) go('default'); setDeleting(null); }).catch((e) => toast('error', e.message)) },
      h('p', null, `删除后 ${deleting.name} 将无法恢复。`)) : null);
  }

  // ------------------------------------------------------------------ batch generation (F9)

  const NW = 168, HEAD = 33, ROW = 28;
  const portY = (n, i) => n.y + HEAD + ROW * i + ROW / 2;
  const nodeRows = (cat, n) => Math.max(cat.nodes[n.type].ins.length, cat.nodes[n.type].outs.length);
  const fieldLabel = (cat, t, k) => ((cat.fields[t] || []).find((f) => f[0] === k) || [k, k])[1];
  const fieldKind = (cat, t, k) => ((cat.fields[t] || []).find((f) => f[0] === k) || [])[2];
  // a filter condition by the field's kind (manager/flow.py FIELDS): num a range, enum one value,
  // text 包含, bool one of the two labels (含图 / 不含图)
  function blankCond(cat, t, field) {
    const k = fieldKind(cat, t, field);
    return k === 'num' ? { field, min: '', max: '' } : k === 'enum' ? { field, op: '=', value: '' } : k === 'bool' ? { field, value: true } : { field, value: '' };
  }
  function condText(cat, t, c) {
    const k = fieldKind(cat, t, c.field), L = fieldLabel(cat, t, c.field), s = (v) => String(v ?? '').trim();
    if (k === 'bool') return (cat.bool[c.field] || [L, '非' + L])[c.value === false ? 1 : 0];
    if (k === 'num') {
      const lo = s(c.min), hi = s(c.max);
      if (lo && hi) return Number(lo) === Number(hi) ? `${L} = ${lo}` : `${L} ${lo}–${hi}`;
      return lo ? `${L} ≥ ${lo}` : hi ? `${L} ≤ ${hi}` : null;
    }
    if (!s(c.value)) return null;
    if (k === 'enum') return `${L} ${c.op === '≠' ? '≠' : '='} ${c.field === 'season' ? SEASON[s(c.value)] || s(c.value) : s(c.value)}`;
    return `${L} 包含 ${s(c.value)}`;
  }

  function paramText(cat, n, inType, inShape, templates, sets, flowName) {
    const p = n.params || {};
    const F = (k) => fieldLabel(cat, inType || 'q', k);
    switch (n.type) {
      case 'bank': return `考试：${p.exam === '*' ? '全部' : p.exam || '9709'}`;
      case 'book': return `教材：${((cat.books.find((b) => b.value === p.book) || {}).label) || p.book || ''}`;
      case 'set': return `题组：${((sets.find((s) => s.id === p.set) || {}).name) || ''}`;
      case 'filter': return (p.conds || []).map((c) => c.field && condText(cat, inType || 'q', c)).filter(Boolean);
      case 'sort': return p.by === 'random' ? ['依据：随机', `种子：${p.seed ?? 1}`] : `依据：${F(p.field || 'marks')}${p.desc ? '降序' : '升序'}`;
      case 'take': return `${inShape === 'group' ? '每组条数' : '条数'}：${p.n ?? 10}`;
      case 'group': return `依据：${F(p.field || 'topic')}`;
      case 'merge': return '';
      case 'join': return `${fieldLabel(cat, 'c', p.left || 'topic')} = ${F(p.right || 'topic')}`;
      case 'export': return `模板：${((templates.find((t) => t.id === (p.template || 'default')) || {}).name) || ''}`;
      case 'newset': return `名称：${flowName || ''}`;
      case 'paper': return '';
      case 'chapters': return [`教材：${!p.book || p.book === '*' ? '全部' : ((cat.books.find((b) => b.value === p.book) || {}).label || p.book)}`, '保存到：exports/chapters'];
      default: return '';
    }
  }

  const TYPE_LABEL = { q: '题目', c: '章节', f: '文件' };
  /** A port's label: what flows through it once known (题目、章节、分组), else the node's own name for it. */
  function portLabel(v, fallback) {
    if (!v || ['左', '右', '附件'].includes(fallback)) return fallback;
    return v.shape === 'group' ? '分组' : TYPE_LABEL[v.type] || fallback;
  }

  // forward: a curve; backward (into a node to the left): out to the right, along the gap
  // between the two nodes, and in from the left, as in the design
  function wirePath(cat, x1, y1, x2, y2, a, b) {
    if (x2 > x1 + 8) { const d = Math.max(32, (x2 - x1) / 2); return `M${x1} ${y1} C${x1 + d} ${y1}, ${x2 - d} ${y2}, ${x2} ${y2}`; }
    let mid = (y1 + y2) / 2;
    if (a && b) {
      const aBottom = a.y + HEAD + ROW * nodeRows(cat, a) + 64, bBottom = b.y + HEAD + ROW * nodeRows(cat, b) + 64;
      mid = b.y > aBottom ? (aBottom + b.y) / 2 : a.y > bBottom ? (bBottom + a.y) / 2 : Math.max(aBottom, bBottom) + 16;
    }
    const r = 8, xo = x1 + 16, xi = x2 - 16, down = mid > y1 ? 1 : -1, back = y2 > mid ? 1 : -1;
    return `M${x1} ${y1} H${xo - r} Q${xo} ${y1} ${xo} ${y1 + r * down} V${mid - r * down} Q${xo} ${mid} ${xo - r} ${mid}` +
      ` H${xi + r} Q${xi} ${mid} ${xi} ${mid + r * back} V${y2 - r * back} Q${xi} ${y2} ${xi + r} ${y2} H${x2}`;
  }

  const countText = (o) => (!o ? '' : o.shape === 'group' ? `${o.count} 组` : String(o.count));

  /** A flow's nodes and wires as elements, with the counts from an evaluation (ev). The
      editor passes its handlers; the overview's preview passes none and is only drawn. */
  function flowParts(g, cat, ev, templates, sets, on = {}) {
    const byId = Object.fromEntries(g.nodes.map((n) => [n.id, n]));
    const ports = (ev && ev.ports) || {};
    const errors = (ev && ev.errors) || {};
    const outOf = (id, i) => (ports[id] || [])[i];
    const inOf = (id, i) => { const l = g.links.find((x) => x.to[0] === id && x.to[1] === i); return l ? outOf(l.from[0], l.from[1]) : null; };
    const shapeOf = (id, i) => { const o = outOf(id, i); return o ? o.shape : cat.nodes[byId[id].type].outs[i][1]; };
    const sel = on.sel;
    const nodes = g.nodes.filter((n) => cat.nodes[n.type]).map((n) => {
      const spec = cat.nodes[n.type];
      const inV = inOf(n.id, 0);
      const ptxt = paramText(cat, n, inV && inV.type, inV && inV.shape, templates, sets, g.name);
      const rows = [];
      for (let i = 0; i < nodeRows(cat, n); i++) {
        const ins = spec.ins[i]; const outs = spec.outs[i];
        const inShape = ins ? ((inOf(n.id, i) || {}).shape || (n.type === 'merge' ? 'group' : 'list')) : null;
        const inLabel = ins ? portLabel(inOf(n.id, i), ins) : null;
        const outLabel = outs ? portLabel(outOf(n.id, i), outs[0]) : null;
        rows.push(h('div', { key: i, className: 'nd-r' },
          ins ? h(React.Fragment, null, h('span', null, inLabel), h('i', { className: `pt l${inShape === 'group' ? ' sq' : ''}`, 'data-in': `${n.id}:${i}` })) : h('span'),
          outs ? h(React.Fragment, null, h('span', null, outLabel, h('b', null, countText(outOf(n.id, i)))),
            h('i', { className: `pt r${shapeOf(n.id, i) === 'group' ? ' sq' : ''}`, onPointerDown: on.startWire ? (e) => on.startWire(e, n, i) : undefined })) : null));
      }
      const lines = [].concat(ptxt).filter((x) => x !== '');
      return h('div', { key: n.id, className: `nd${sel && sel.node === n.id ? ' sel' : ''}${errors[n.id] ? ' err' : ''}`, style: { left: n.x, top: n.y, width: NW },
        onPointerDown: on.startMove ? (e) => { if (!e.target.classList.contains('pt')) on.startMove(e, n); } : undefined },
      h('div', { className: 'nd-h' }, spec.label), rows,
      lines.length ? h('div', { className: 'nd-p' }, lines.map((t, i) => h('div', { key: i }, t))) : null);
    });
    const wires = g.links.map((l, i) => {
      const a = byId[l.from[0]], b = byId[l.to[0]];
      if (!a || !b || !cat.nodes[a.type] || !cat.nodes[b.type]) return null;
      const d = wirePath(cat, a.x + NW + 1, portY(a, l.from[1]), b.x - 1, portY(b, l.to[1]), a, b);
      return h('path', { key: i, d, className: `${shapeOf(a.id, l.from[1]) === 'group' ? 'g' : ''}${sel && sel.link === i ? ' sel' : ''}`,
        onPointerDown: on.selectLink ? (e) => { e.stopPropagation(); on.selectLink(i); } : undefined });
    });
    return { nodes, wires };
  }

  /** The overview's picture of a flow: the graph scaled to fit a fixed-height box, not editable. */
  function FlowPreview({ g, cat, templates, sets }) {
    const [ev, setEv] = useState(null);
    const [width, setWidth] = useState(0);
    const box = useRef(null);
    useEffect(() => { send('POST', '/api/flows/eval', g).then(setEv).catch(() => {}); }, [g.id]);
    useEffect(() => {
      const ro = new ResizeObserver(([e]) => setWidth(e.contentRect.width));
      if (box.current) ro.observe(box.current);
      return () => ro.disconnect();
    }, []);
    // the nodes' extent (a node's parameter lines are not measured: about 64 px below its ports)
    const PAD = 24, HIGH = 392;
    const x0 = Math.min(...g.nodes.map((n) => n.x)), y0 = Math.min(...g.nodes.map((n) => n.y));
    const x1 = Math.max(...g.nodes.map((n) => n.x + NW)), y1 = Math.max(...g.nodes.map((n) => n.y + HEAD + ROW * nodeRows(cat, n) + 64));
    const w = x1 - x0, hgt = y1 - y0;
    const scale = Math.min(1, (width - 2 * PAD) / w, (HIGH - 2 * PAD) / hgt) || 1;
    const { nodes, wires } = flowParts(g, cat, ev, templates, sets);
    return h('div', { ref: box, className: 'fl fl-pv', 'aria-label': '流程图' },
      g.nodes.length ? h('div', { className: 'fl-in', style: { width: x1, height: y1, transformOrigin: '0 0',
        transform: `translate(${PAD - x0 * scale}px, ${(HIGH - hgt * scale) / 2 - y0 * scale}px) scale(${scale})` } },
      h('svg', { className: 'fl-w', width: x1 + 64, height: y1 + 64 }, wires), nodes)
        : h(E.EmptyState, { icon: 'i-grid', title: '没有节点' }));
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
    const [dialog, setDialog] = useState(null);   // 'rename' | 'delete'
    const [name, setName] = useState('');
    const box = useRef(null);
    const nid = useRef(1);

    useEffect(() => { api('/api/flows/catalog').then(setCat); }, []);
    // changes are saved as they are made (built-in flows are read-only); a change still
    // waiting is saved at once when the page is left
    const pending = useRef(null);
    useEffect(() => {
      if (!g || g.builtin) return undefined;
      const text = JSON.stringify(g);
      if (text === saved) return undefined;
      const save = () => { clearTimeout(tm); pending.current = null; return send('PUT', '/api/flows/' + g.id, g).then(() => setSaved(text)).catch((e) => toast('error', e.message)); };
      const tm = setTimeout(save, 800);
      pending.current = save;
      return () => { clearTimeout(tm); };
    }, [g, saved]);
    useEffect(() => () => { if (pending.current) pending.current(); }, []);
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
      if (!sel || !g || g.builtin) return;
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
    if (g === false) return h('div', { className: 'dm-row' }, h(E.EmptyState, { icon: 'i-doc', title: '流程不存在' }));
    if (!g || !cat) return h('div', { className: 'dm-row' }, h(E.Loading, null));

    const byId = Object.fromEntries(g.nodes.map((n) => [n.id, n]));
    const ports = (ev && ev.ports) || {};
    const errors = (ev && ev.errors) || {};
    const outOf = (id, i) => (ports[id] || [])[i];
    const inOf = (id, i) => { const l = g.links.find((x) => x.to[0] === id && x.to[1] === i); return l ? outOf(l.from[0], l.from[1]) : null; };
    // a built-in flow can be looked at and run, not changed
    const update = (id, patch) => !g.builtin && setG({ ...g, nodes: g.nodes.map((n) => (n.id === id ? { ...n, params: { ...n.params, ...patch } } : n)) });

    const add = (type) => {
      if (g.builtin) return;
      const el = box.current;
      const x = (el ? el.scrollLeft : 0) + 32 + (g.nodes.length % 4) * 24;
      const y = (el ? el.scrollTop : 0) + 32 + (g.nodes.length % 4) * 24;
      const id = 'n' + nid.current++;
      const params = { bank: { exam: '9709' }, book: { book: '9709_p1' }, filter: { conds: [{ field: 'year', min: '', max: '' }] },
        sort: { by: 'field', field: 'marks', desc: true }, take: { n: 10 }, group: { field: 'topic' },
        join: { left: 'topic', right: 'topic' }, export: { template: 'default' }, chapters: { book: '*' },
        set: { set: sets[0] ? sets[0].id : '' } }[type] || {};
      setG({ ...g, nodes: g.nodes.concat([{ id, type, x: Math.round(x), y: Math.round(y), params }]) });
      setSel({ node: id });
    };

    const local = (e) => { const r = box.current.getBoundingClientRect(); return [e.clientX - r.left + box.current.scrollLeft, e.clientY - r.top + box.current.scrollTop]; };
    const startMove = (e, n) => {
      if (e.button !== 0) return;
      e.preventDefault();
      setSel({ node: n.id });
      if (g.builtin) return;
      const [sx, sy] = local(e); const ox = n.x, oy = n.y;
      const move = (ev2) => { const [x, y] = local(ev2); setG((cur) => ({ ...cur, nodes: cur.nodes.map((m) => (m.id === n.id ? { ...m, x: Math.max(8, Math.round(ox + x - sx)), y: Math.max(8, Math.round(oy + y - sy)) } : m)) })); };
      const up = () => { removeEventListener('pointermove', move); removeEventListener('pointerup', up); };
      addEventListener('pointermove', move); addEventListener('pointerup', up);
    };
    const startWire = (e, n, i) => {
      if (g.builtin) return;
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

    const W = Math.max(960, ...g.nodes.map((n) => n.x + NW + 240));
    const H = Math.max(560, ...g.nodes.map((n) => n.y + 280));
    const { nodes: nodeEls, wires } = flowParts(g, cat, ev, templates, sets, {
      sel, startMove, startWire, selectLink: (i) => setSel({ link: i }) });
    if (drag) {
      const a = byId[drag.from[0]];
      wires.push(h('path', { key: 'drag', className: 'drag', d: wirePath(cat, a.x + NW + 1, portY(a, drag.from[1]), drag.x, drag.y) }));
    }

    const doRun = () => {
      setRunning(true);
      send('POST', `/api/flows/${g.id}/run`, g).then((r) => { setRun(r); setEv(r); reloadSets(); })
        .catch((e) => toast('error', e.message)).finally(() => setRunning(false));
    };

    const outputs = (run && run.outputs) || [];
    const failed = run && failure(run, (id) => byId[id] && cat.nodes[byId[id].type].label);
    const overview = '#/templates/flows/' + g.id;
    // 完成: the change still waiting is saved before the overview opens
    const done = () => Promise.resolve(pending.current && pending.current()).then(() => { location.hash = overview; });
    const copy = () => send('POST', '/api/flows', { ...g, name: g.name + ' 副本', builtin: undefined, summary: undefined })
      .then((n) => { location.hash = '#/flows/' + n.id; }).catch((e) => toast('error', e.message));
    const saveState = g.builtin ? null : JSON.stringify(g) === saved ? '已保存' : '正在保存';
    return h('div', { className: 'dm-row flowpage' + (g.builtin ? ' is-locked' : '') },
      h('aside', { className: 'fl-pal' },
        ['来源', '处理', '输出'].map((c) => h(React.Fragment, { key: c },
          h('span', { className: 'fs-small fl-cat' }, c),
          Object.entries(cat.nodes).filter(([, v]) => v.cat === c).map(([k, v]) =>
            h('button', { key: k, type: 'button', className: 'pal', disabled: g.builtin, onClick: () => add(k) }, v.label))))),
      h('main', { className: 'fl-main' },
        h('div', { className: 'fl-bar' },
          failed ? h('div', { className: 'dm-grow' }, h(E.Banner, { type: 'error', title: failed }))
            : h('div', { className: 'dm-meta', style: { flexGrow: 1 } },
              saveState ? h('span', null, saveState) : null,
              run ? h('span', null, `${run.ran} 运行，${outputs.length} 项输出`) : null),
          act('i-copy', '复制 JSON', () => copyFlow(g, toast)),
          h(MoreMenu, { label: '更多操作', items: [
            g.builtin ? null : { label: '重命名', onClick: () => { setName(g.name); setDialog('rename'); } },
            { label: '复制流程', onClick: copy },
            { label: '下载 JSON', onClick: () => saveFlow(g) },
            g.builtin ? null : { label: '删除流程', danger: true, onClick: () => setDialog('delete') }] }),
          h(E.Button, { variant: 'primary', size: 'sm', disabled: running, loading: running, onClick: doRun }, '运行流程'),
          h(E.Button, { variant: 'secondary', size: 'sm', onClick: done }, '完成')),
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
            nodeEls)),
        outputs.length ? h('section', { className: 'outs' },
          h('h2', { className: 'fs-lead', style: { margin: 0 } }, '输出'),
          h(FlowOutputs, { fid: g.id, outputs })) : null),
      h('aside', { className: 'fl-insp' },
        sel && sel.link != null && g.links[sel.link]
          ? h(React.Fragment, null,
            h('div', { className: 'panel-row' },
              h('h2', { className: 'fs-lead panel-title' }, '连线'),
              g.builtin ? null : act('i-trash', '删除连线', del)),
            h('div', { className: 'dm-meta' },
              h('span', null, cat.nodes[byId[g.links[sel.link].from[0]].type].label), h(E.Icon, { name: 'i-arrow-r', size: 'sm' }),
              h('span', null, cat.nodes[byId[g.links[sel.link].to[0]].type].label)))
          : sel && sel.node && byId[sel.node]
          ? h(Inspector, { cat, n: byId[sel.node], inV: inOf(sel.node, 0), in2: inOf(sel.node, 1), out: outOf(sel.node, 0),
            error: errors[sel.node], update, templates, sets, onDelete: del, locked: g.builtin, outputs: outputs.filter((o) => o.node === sel.node) })
          : h(E.EmptyState, { icon: 'i-grid', title: '未选择节点' })),
      dialog === 'rename' ? h(E.Dialog, { open: true, title: '重命名流程', confirmLabel: '重命名', onClose: () => setDialog(null),
        onConfirm: () => { if (name.trim()) setG({ ...g, name: name.trim() }); } },
      h(E.TextField, { label: '名称', size: 'sm', value: name, autoFocus: true, onChange: (e) => setName(e.target.value) })) : null,
      dialog === 'delete' ? h(E.Dialog, { open: true, danger: true, title: '删除流程', confirmLabel: '删除流程', onClose: () => setDialog(null),
        onConfirm: () => { pending.current = null; send('DELETE', '/api/flows/' + g.id).then(() => { location.hash = '#/templates/flows'; }).catch((e) => toast('error', e.message)); } },
      h('p', null, `删除后 ${g.name} 将无法恢复。`)) : null);
  }

  /** A flow as JSON, as it is saved: its name, nodes and links. */
  const flowJson = (g) => JSON.stringify({ name: g.name,
    nodes: g.nodes.map(({ id, type, x, y, params }) => ({ id, type, x, y, params })), links: g.links }, null, 1);
  const saveFlow = (g) => {
    const a = document.createElement('a');
    a.href = URL.createObjectURL(new Blob([flowJson(g)], { type: 'application/json' }));
    a.download = g.name + '.json';
    document.body.appendChild(a); a.click(); a.remove();
    setTimeout(() => URL.revokeObjectURL(a.href), 1000);
  };
  const copyFlow = (g, toast) => {
    try {
      copyText(flowJson(g)).then(() => toast('success', 'JSON 已复制'), () => toast('error', 'JSON 无法复制'));
    } catch (e) { toast('error', 'JSON 无法复制'); }
  };

  /** "流程无法运行（节点：原因）" for a run with errors, else null. */
  function failure(run, label) {
    const [id, why] = Object.entries(run.errors || {})[0] || [];
    return id ? `流程无法运行（${label(id) || id}：${why}）` : null;
  }

  /** What a run made: each file to download, each set to open. */
  function FlowOutputs({ fid, outputs }) {
    return h('div', { className: 'fo-list' }, outputs.map((o, i) => h('div', { key: i, className: 'fo-row' },
      h('span', { className: 'fo-name' }, o.name),
      h('div', { className: 'dm-meta' }, o.meta.map((m, j) => h('span', { key: j }, m))),
      o.kind === 'folder' ? null
        : o.kind === 'set'
        ? act('i-arrow-r', '打开题组', () => { location.hash = '#/sets/' + o.set; })
        : act(o.kind === 'zip' ? 'i-box' : 'i-doc', o.kind === 'zip' ? '下载 ZIP' : '下载 PDF',
          () => download(`/api/flows/${fid}/out/${o.file}?name=${encodeURIComponent(o.name)}`)))));
  }

  function Inspector({ cat, n, inV, in2, out, error, update, templates, sets, onDelete, outputs, locked }) {
    const spec = cat.nodes[n.type];
    const p = n.params || {};
    const t = (inV && inV.type) || 'q';
    const fields = (cat.fields[t] || []).map(([v, label]) => ({ value: v, label }));
    // an error about the node's one parameter is shown on that field, others below the fields
    const fieldErr = error && !/输入/.test(error) && ['bank', 'book', 'set', 'take', 'export', 'chapters'].includes(n.type) ? error : null;
    const sel = (label, value, options, onChange) => h(E.Select, { label, size: 'sm', value, options, onChange, error: fieldErr || undefined });
    let body = null;
    if (n.type === 'bank') body = sel('考试', p.exam || '9709', [{ value: '*', label: '全部' }].concat(cat.exams.map((e) => ({ value: e, label: e }))), (v) => update(n.id, { exam: v }));
    if (n.type === 'chapters') body = sel('教材', p.book || '*', [{ value: '*', label: '全部教材' }].concat(cat.books.map((b) => ({ value: b.value, label: b.label }))), (v) => update(n.id, { book: v }));
    if (n.type === 'book') body = sel('教材', p.book || '9709_p1', cat.books.map((b) => ({ value: b.value, label: b.label })), (v) => update(n.id, { book: v }));
    if (n.type === 'set') body = sel('题组', p.set || '', sets.map((s) => ({ value: s.id, label: s.name })), (v) => update(n.id, { set: v }));
    if (n.type === 'filter') {
      const conds = p.conds || [];
      const put = (i, c) => update(n.id, { conds: conds.map((x, j) => (j === i ? c : x)) });
      const vals = (inV && inV.values) || {};
      const row = (c, i) => {
        const k = fieldKind(cat, t, c.field);
        const tf = (label, key) => h(E.TextField, { 'aria-label': label, placeholder: label, size: 'sm', value: String(c[key] ?? ''), onChange: (e) => put(i, { ...c, [key]: e.target.value }) });
        if (k === 'num') return h('div', { className: 'years' }, tf('最小', 'min'), h('span', null, '至'), tf('最大', 'max'));
        if (k === 'bool') {
          const [yes, no] = cat.bool[c.field] || ['是', '否'];
          return h(E.SegmentedControl, { ariaLabel: fieldLabel(cat, t, c.field), value: c.value === false ? 'no' : 'yes', onChange: (v) => put(i, { ...c, value: v === 'yes' }),
            options: [{ value: 'yes', label: yes }, { value: 'no', label: no }] });
        }
        if (k === 'enum') {
          const opts = (vals[c.field] || []).map(([v, label]) => ({ value: v, label }));
          if (c.value && !opts.some((o) => o.value === String(c.value))) opts.unshift({ value: String(c.value), label: String(c.value) });
          return h('div', { className: 'cond-e' },
            h(E.Select, { ariaLabel: '是否', size: 'sm', value: c.op === '≠' ? '≠' : '=', options: [{ value: '=', label: '是' }, { value: '≠', label: '不是' }], onChange: (v) => put(i, { ...c, op: v }) }),
            h(E.Select, { ariaLabel: fieldLabel(cat, t, c.field), placeholder: '未选择', size: 'sm', value: String(c.value ?? ''), options: opts, onChange: (v) => put(i, { ...c, value: v }) }));
        }
        return h('div', { className: 'cond-e' }, h('span', { className: 'cond-op' }, '包含'), tf('文字', 'value'));
      };
      body = h('div', { style: { display: 'flex', flexDirection: 'column', gap: 'var(--el)' } },
        h('div', { className: 'panel-row' },
          h('span', { className: 'fs-small panel-title' }, '条件'),
          act('i-plus', '添加条件', () => update(n.id, { conds: conds.concat([blankCond(cat, t, fields[0] ? fields[0].value : 'year')]) }))),
        conds.map((c, i) => h('div', { key: i, className: 'cond' },
          h('div', { className: 'cond-f' }, h(E.Select, { ariaLabel: '字段', size: 'sm', value: c.field, options: fields, onChange: (v) => put(i, blankCond(cat, t, v)) })),
          h('div', { className: 'cond-d' }, h(E.IconButton, { icon: 'i-close', label: '删除条件', variant: 'ghost', size: 'sm', onClick: () => update(n.id, { conds: conds.filter((_, j) => j !== i) }) })),
          h('div', { className: 'cond-v' }, row(c, i)))));
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
    if (n.type === 'take') body = h(E.TextField, { label: '条数', size: 'sm', error: fieldErr || undefined, value: String(p.n ?? 10), onChange: (e) => update(n.id, { n: e.target.value }) });
    if (n.type === 'group') body = sel('字段', p.field || 'topic', fields, (v) => update(n.id, { field: v }));
    if (n.type === 'join') {
      const lt = (inV && inV.type) || 'c', rt = (in2 && in2.type) || 'q';
      body = h(React.Fragment, null,
        sel('左侧字段', p.left || 'topic', (cat.fields[lt] || []).map(([v, l]) => ({ value: v, label: l })), (v) => update(n.id, { left: v })),
        sel('右侧字段', p.right || 'topic', (cat.fields[rt] || []).map(([v, l]) => ({ value: v, label: l })), (v) => update(n.id, { right: v })));
    }
    if (n.type === 'export') body = sel('导出模板', p.template || 'default', templates.map((x) => ({ value: x.id, label: x.name })), (v) => update(n.id, { template: v }));

    const shown = out || (spec.outs.length ? null : inV);
    return h(React.Fragment, null,
      h('div', { className: 'panel-row' },
        h('h2', { className: 'fs-lead panel-title' }, spec.label),
        locked ? null : act('i-trash', '删除节点', onDelete)),
      locked ? h('p', { className: 'lock-note' }, '内置流程不可修改，在流程列表中复制流程后可修改副本') : null,
      body ? h('div', { className: locked ? 'locked' : undefined, style: { display: 'flex', flexDirection: 'column', gap: 'var(--sub)' } }, body) : null,
      error && !fieldErr ? h('div', { className: 'fl-err fs-small' }, error) : null,
      shown ? h('div', { className: 'sum' },
        h('div', { className: 'dm-meta' }, shown.shape === 'group'
          ? [h('span', { key: 'a' }, h('b', null, shown.count), ' 组'), h('span', { key: 'b' }, h('b', null, shown.items), shown.type === 'q' ? ' 题' : ' 条')]
          : [h('span', { key: 'a' }, h('b', null, shown.count), shown.type === 'q' ? ' 题' : ' 条')]),
        h('div', { className: 'res' }, shown.rows.map((r, i) => h(React.Fragment, { key: i }, h('span', null, r[0]))))) : null,
      outputs.length ? h('div', { className: 'sum' }, outputs.map((o, i) => h('div', { key: i, className: 'dm-meta' }, h('span', null, o.name), o.meta.map((m, j) => h('span', { key: j }, m))))) : null);
  }

  /** The flows: the list, and the one picked with its conditions, what it makes and the
      two actions, 编辑流程 and 运行流程. */
  function FlowListPage({ current, reloadSets, templates, sets, toast }) {
    const [flows, setFlows] = useState(null);
    const [renameId, setRenameId] = useState(null);     // 重命名流程 from a list item's menu
    const [deleting, setDeleting] = useState(null);
    const reload = () => api('/api/flows').then(setFlows);
    useEffect(() => { reload(); }, []);
    const go = (id) => { location.hash = '#/templates/flows/' + id; };
    const create = () => send('POST', '/api/flows', { name: '未命名流程', nodes: [], links: [] })
      .then((n) => { location.hash = '#/flows/' + n.id; }).catch((e) => toast('error', e.message));
    const copy = (x) => api('/api/flows/' + x.id).then((g) => send('POST', '/api/flows', { ...g, name: g.name + ' 副本', builtin: undefined, summary: undefined }))
      .then((n) => reload().then(() => go(n.id))).catch((e) => toast('error', e.message));
    const f = flows && (flows.find((x) => x.id === current) || flows[0]);
    return h('div', { className: 'dm-row tplpage' },
      h('aside', { className: 'tpl-list' },
        h(KindTabs, { value: 'flow' }),
        h('div', { className: 'setlist-acts' }, h(E.Button, { variant: 'secondary', size: 'sm', icon: 'i-plus', onClick: create }, '新建流程')),
        !flows ? h(E.Loading, null) : flows.length ? h(E.List, { variant: 'two-line', selectable: true, ariaLabel: '流程', value: f && f.id,
          onChange: go,
          items: flows.map((x) => ({ value: x.id, icon: 'i-grid', title: x.name, subtitle: x.summary,
            trailing: h(MoreMenu, { label: '更多操作', tip: false, items: [
              x.builtin ? null : { label: '重命名', onClick: () => { setRenameId(x.id); go(x.id); } },
              { label: '复制流程', onClick: () => copy(x) },
              x.builtin ? null : { label: '删除流程', danger: true, onClick: () => setDeleting(x) }] }) })) })
          : h(E.EmptyState, { icon: 'i-grid', title: '没有流程' })),
      f ? h(FlowOverview, { key: f.id, fid: f.id, reload, reloadSets, templates, sets, toast, rename: renameId === f.id, onRename: () => setRenameId(null) })
        : h('main', { className: 'setmain empty-main' }, flows ? h(E.EmptyState, { icon: 'i-grid', title: '没有流程' }) : null),
      deleting ? h(E.Dialog, { open: true, danger: true, title: '删除流程', confirmLabel: '删除流程', onClose: () => setDeleting(null),
        onConfirm: () => send('DELETE', '/api/flows/' + deleting.id).then(() => reload())
          .then(() => { if (f && f.id === deleting.id) location.hash = '#/templates/flows'; setDeleting(null); })
          .catch((e) => toast('error', e.message)) },
      h('p', null, `删除后 ${deleting.name} 将无法恢复。`)) : null);
  }

  /** A flow picked in the list: its name and conditions, 编辑流程 and 运行流程, a picture of
      the graph, and what the last run made. */
  function FlowOverview({ fid, reload, reloadSets, templates, sets, toast, rename, onRename }) {
    const [g, setG] = useState(null);
    const [last, setLast] = useState(undefined);       // the last run: {ran, errors, outputs}, null: never run
    const [running, setRunning] = useState(false);
    const [renaming, setRenaming] = useState(false);
    const [cat, setCat] = useState(null);
    useEffect(() => { api('/api/flows/' + fid).then(setG).catch(() => setG(false)); }, [fid]);
    useEffect(() => { api(`/api/flows/${fid}/last`).then(setLast).catch(() => setLast(null)); }, [fid]);
    useEffect(() => { api('/api/flows/catalog').then(setCat); }, []);
    useEffect(() => { if (rename && g) { setRenaming(true); onRename(); } }, [rename, !!g]);
    if (g === false) return h('main', { className: 'setmain empty-main' }, h(E.EmptyState, { icon: 'i-doc', title: '流程不存在' }));
    if (!g || !cat) return h('main', { className: 'setmain' }, h(E.Loading, null));
    const doRun = () => {
      setRunning(true);
      send('POST', `/api/flows/${g.id}/run`, g).then((r) => { setLast(r); reloadSets(); })
        .catch((e) => toast('error', e.message)).finally(() => setRunning(false));
    };
    const saveName = (name) => send('PUT', '/api/flows/' + g.id, { ...g, name })
      .then((n) => { setG({ ...g, name: n.name }); reload(); }).catch((e) => toast('error', e.message));
    const failed = last && failure(last, (id) => { const n = g.nodes.find((x) => x.id === id); return n && cat.nodes[n.type] && cat.nodes[n.type].label; });
    return h('main', { className: 'setmain fo' },
      h('header', { className: 'fo-head' },
        h('div', { className: 'page-head dm-grow' },
          h(EditableTitle, { value: g.name, readOnly: g.builtin, editing: renaming, setEditing: setRenaming, label: '重命名流程', onSave: saveName }),
          h('div', { className: 'dm-meta' }, g.summary ? h('span', null, g.summary) : null, last ? h('span', { className: 't' }, last.ran) : null)),
        h(E.Button, { variant: 'primary', size: 'md', icon: 'i-edit', onClick: () => { location.hash = '#/flows/' + g.id; } }, '编辑流程'),
        h(E.Button, { variant: 'primary', size: 'md', disabled: running, loading: running, onClick: doRun }, '运行流程'),
        act('i-copy', '复制 JSON', () => copyFlow(g, toast))),
      h(FlowPreview, { key: g.id, g, cat, templates, sets }),
      h('section', { className: 'fo-sec' },
        h('h2', { className: 'fs-lead fo-title' }, '上次输出'),
        running ? h(E.Loading, { label: '正在运行流程' })
          : last === undefined ? h(E.Loading, null)
          : !last ? h('span', { className: 'empty-note' }, '未运行流程')
          : failed ? h(E.Banner, { type: 'error', title: failed })
          : h(FlowOutputs, { fid: g.id, outputs: last.outputs })));
  }

  function KindTabs({ value }) {
    return h(E.Tabs, { variant: 'line', value, ariaLabel: '模板类型', items: [{ value: 'export', label: '导出' }, { value: 'flow', label: '批量生成' }],
      onChange: (v) => { location.hash = v === 'flow' ? '#/templates/flows' : '#/templates'; } });
  }

  /** 版面 (docs/ui-text.md 4.8): the practice paper's answer space, four steps from 紧凑 to
      宽松 (the original paper's answer space): four segments in a row, filled up to the
      step chosen. A click picks a step; the arrow keys, Home and End move it. */
  function SpaceSlider({ value, onChange }) {
    const NAMES = ['紧凑', '原卷答题区的四分之一', '原卷答题区的一半', '宽松，即原卷答题区'];
    const key = (e) => {
      const to = { ArrowLeft: value - 1, ArrowDown: value - 1, ArrowRight: value + 1, ArrowUp: value + 1, Home: 0, End: 3 }[e.key];
      if (to === undefined) return;
      e.preventDefault();
      onChange(Math.max(0, Math.min(3, to)));
    };
    return h('fieldset', { className: 'opt-group ex space' }, h('legend', null, '版面'),
      h('div', { className: 'space-bar', role: 'slider', tabIndex: 0, 'aria-label': '版面', 'aria-valuemin': 0, 'aria-valuemax': 3,
        'aria-valuenow': value, 'aria-valuetext': NAMES[value], onKeyDown: key },
        [0, 1, 2, 3].map((n) => h('button', { key: n, type: 'button', tabIndex: -1, className: 'space-cell' + (n <= value ? ' on' : ''),
          'aria-label': NAMES[n], onClick: () => onChange(n) }, h('i')))),
      h('div', { className: 'space-ends', 'aria-hidden': 'true' },
        h('span', null, '紧凑'), h('span', null, '宽松')));
  }

  /** Settings: the options on the left, a practice paper of the first set that has
      questions on the right, redrawn as the footer options change. */
  function SettingsPage({ sets }) {
    const [o, setO] = useState(null);
    const [shown, setShown] = useState(null);           // {bits, pages}: the preview on screen
    useEffect(() => { api('/api/settings').then(setO); }, []);
    const loaded = useRef(null);
    useEffect(() => {
      if (!o) return undefined;
      if (!loaded.current) { loaded.current = JSON.stringify(o); return undefined; }
      const t = setTimeout(() => send('PUT', '/api/settings', o), 300);
      return () => clearTimeout(t);
    }, [o && JSON.stringify(o)]);
    const sample = sets.find((x) => x.count);
    const foot = o ? [o.footer_name, o.footer_code, o.footer_page].map(Number).join('') + o.space : '';
    // the preview of the new options replaces the old one only when its pages have loaded
    useEffect(() => {
      if (!o || !sample) return undefined;
      let live = true;
      api(`/api/settings/preview/${foot}`).then((p) => Promise.all(Array.from({ length: p.pages }, (_, n) => new Promise((ok) => {
        const img = new Image(); img.onload = img.onerror = ok; img.src = `/api/settings/preview/${foot}/${n}.png`;
      }))).then(() => { if (live) setShown({ bits: foot, pages: p.pages }); })).catch(() => { if (live) setShown({ bits: foot, pages: 0 }); });
      return () => { live = false; };
    }, [foot, sample && sample.id]);
    if (!o) return h(E.Loading, null);
    // the page follows the choice at once; the settings are saved once the choices settle
    const put = (k, v) => {
      setO((cur) => ({ ...cur, [k]: v }));
      if (k === 'theme') applyTheme(v);
    };
    const box = (key, label) => h(E.Checkbox, { checked: o[key], onChange: () => put(key, !o[key]) }, label);
    return h(React.Fragment, null,
      h('section', { className: 'st-opts' },
        h(SpaceSlider, { value: o.space, onChange: (v) => put('space', v) }),
        h('fieldset', { className: 'opt-group ex' }, h('legend', null, '页脚显示'),
          box('footer_name', '题组名称'), box('footer_code', '试卷代码与题号'), box('footer_page', '页码')),
        h('fieldset', { className: 'opt-group ex' }, h('legend', null, '配色'),
          h(E.SegmentedControl, { ariaLabel: '配色', value: o.theme, onChange: (v) => put('theme', v),
            options: [{ value: 'system', label: '自动' }, { value: 'light', label: '浅色' }, { value: 'dark', label: '深色' }] }))),
      h('section', { className: 'st-preview' },
        h('h2', { className: 'fs-lead st-title' }, '练习卷预览'),
        !sample ? h(E.EmptyState, { icon: 'i-list', title: '没有题组' })
          : !shown ? h(E.Loading, { label: '正在生成练习卷' })
          : h('div', { className: 'sd-sheets' }, Array.from({ length: shown.pages }, (_, n) =>
            h('img', { key: n, className: 'sheet', src: `/api/settings/preview/${shown.bits}/${n}.png`, alt: `第 ${n + 1} 页` })))));
  }

  const afterBoot = (f) => (window.dmBoot ? dmBoot.after(f) : f());

  let theme = 'system';
  function applyTheme(t) {
    theme = t;
    try { localStorage.setItem('dm-theme', t); } catch (e) {}
    const light = t === 'light' || (t === 'system' && matchMedia('(prefers-color-scheme: light)').matches);
    document.documentElement.setAttribute('data-theme', light ? 'light' : 'dark');
  }

  matchMedia('(prefers-color-scheme: light)').addEventListener('change', () => { if (theme === 'system') applyTheme('system'); });

  // ------------------------------------------------------------------ shell

  function App() {
    const hash = useHash();
    const toast = E.useToast();
    const [metas, setMetas] = useState(null);
    const [sets, setSets] = useState([]);
    const [templates, setTemplates] = useState([]);
    const [flowTitle, setFlowTitle] = useState('');
    const [acts, setActs] = useState(null);        // the top bar's action slot, for the pages' actions
    useEffect(() => { if (metas && window.dmBoot) dmBoot.ready(); }, [metas]);   // index.html's loader
    const reloadSets = useCallback(() => api('/api/sets').then(setSets), []);
    const reloadTemplates = useCallback(() => api('/api/templates').then(setTemplates), []);
    useEffect(() => { api('/api/meta').then(setMetas); reloadSets(); reloadTemplates(); api('/api/settings').then((o) => applyTheme(o.theme)); }, []);

    const PAGES = ['query', 'search', 'sets', 'templates', 'flows', 'settings'];
    const page = hash.split('/')[1] || 'query';
    const [, , arg, sub, subArg] = hash.split('/');
    // an address that names no page goes to the query page
    useEffect(() => { if (!PAGES.includes(page)) location.replace('#/query'); }, [page]);
    // a set's address with an unknown part (the former practice paper and export pages) goes to the set
    useEffect(() => { if (page === 'sets' && sub && sub !== 'board') location.replace('#/sets/' + arg); }, [page, sub]);
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
    const nav = [
      { value: 'query', label: '查询', icon: 'i-filter', href: '#/query' },
      { value: 'search', label: '搜索', icon: 'i-search', href: '#/search' },
      { value: 'sets', label: '题组', icon: 'i-list', href: '#/sets' },
      { value: 'templates', label: '模板', icon: 'i-doc', href: '#/templates' },
    ];
    const titles = { query: '查询', search: '搜索', sets: '题组', templates: '模板', settings: '设置' };
    const cur = page === 'sets' ? sets.find((x) => x.id === arg) : null;
    let body;
    if (!metas) body = null;
    else if (page === 'sets' && sub === 'board') {
      body = cur ? h(BoardPage, { key: subArg, s: cur, bid: subArg, acts }) : h(E.Loading, null);
    } else if (page === 'sets') body = h(SetsPage, { sets, current: arg, reloadSets, templates, toast });
    else if (page === 'templates' && arg === 'flows') body = (templates.length ? h(FlowListPage, { current: sub, reloadSets, templates, sets, toast }) : h(E.Loading, null));
    else if (page === 'flows') body = templates.length ? h(FlowPage, { key: arg, fid: arg, templates, sets, reloadSets, toast, onTitle: setFlowTitle }) : h(E.Loading, null);
    else if (page === 'templates') {
      body = templates.length ? h(TemplatesPage, { templates, current: arg, reloadTemplates, sets, toast }) : h(E.Loading, null);
    } else if (page === 'settings') body = h('div', { className: 'dm-row' }, h(SettingsPage, { sets }));
    else if (page === 'query') body = h(QueryPage, { metas, sets, reloadSets, toast });
    else if (page === 'search') body = h(SearchPage, { metas, sets, reloadSets, toast });
    else body = null;
    const SUB = { board: '白板' };
    const title = page === 'sets' && SUB[sub] ? SUB[sub] : page === 'flows' ? (flowTitle || '批量生成') : (titles[page] || '查询');
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
          crumbs: page === 'sets' && SUB[sub] && cur
            ? [{ label: '题组', href: '#/sets/' + arg }, { label: cur.name, href: '#/sets/' + arg }, { label: SUB[sub] }]
            : page === 'flows' ? [{ label: '模板', href: '#/templates' }, { label: '批量生成', href: '#/templates/flows/' + arg }] : undefined,
          actions: h('div', { ref: setActs, className: 'dm-acts' }) }),
        body));
  }

  ReactDOM.createRoot(document.getElementById('root')).render(h(E.ToastProvider, null, h(App)));
})();
