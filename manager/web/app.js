/* 题库数据管理 (docs/data-manager.md). React without a build step: h = createElement.
   Pages: #/query, #/sets/<id>. */
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

  function QueryPage({ metas, search, sets, reloadSets, toast }) {
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
      api(`/api/search?exam=${exam}&q=${encodeURIComponent(search)}`).then((ids) => setHits({ ids: new Set(ids) }));
    }, [search, exam]);

    const changeExam = (v) => {
      setExam(v); setF(defaults(metas.find((m) => m.exam === v))); setSelected([]); setFocus(null);
    };
    const setComponents = (next) => {
      const topics = new Set(meta.topics.filter((t) => next.has(t.component)).map((t) => t.value));
      setF({ ...f, components: next, topics });
    };

    const taskItems = useMemo(() => {
      const n = {};
      allRows.forEach((r) => {
        if (f.components.has(r.component) && r.year >= f.from && r.year <= f.to) r.tasks.forEach((t) => { n[t] = (n[t] || 0) + 1; });
      });
      return Object.keys(n).sort((a, b) => n[b] - n[a]).map((t) => ({
        value: t, label: t.replace(/_/g, ' ').replace(/^./, (c) => c.toUpperCase()), n: n[t],
      }));
    }, [allRows, f.components, f.from, f.to]);
    const tasks = f.tasks || new Set(taskItems.map((t) => t.value));

    const rows = useMemo(() => allRows.filter((r) => {
      if (!f.components.has(r.component) || r.year < f.from || r.year > f.to) return false;
      if (r.topic && !f.topics.has(r.topic)) return false;
      if (taskItems.length && r.tasks.length && !r.tasks.some((t) => tasks.has(t))) return false;
      if (hits && hits.ids && !hits.ids.has(r.id)) return false;
      if (hits && hits.code) {
        const c = hits.code;
        if (r.month !== c.season || r.year % 100 !== c.yy || r.paper !== c.paper) return false;
        if (c.q && r.q !== c.q) return false;
      }
      return true;
    }), [allRows, f, tasks, hits, taskItems]);
    const view = useMemo(() => rows
      .slice().sort((a, b) => b.year - a.year || a.month - b.month || a.paper.localeCompare(b.paper) || a.q - b.q)
      .map((r) => ({ ...r, season: MONTH[r.month] || r.month + ' 月', qn: 'Q' + r.q })), [rows]);

    const picked = allRows.filter((r) => selected.includes(r.id));
    const onSelected = (keys) => {
      const added = keys.filter((k) => !selected.includes(k));
      if (added.length === 1) setFocus(added[0]);
      setSelected(keys);
    };
    useEffect(() => { if (!focus && view.length) setFocus(null); }, [view]);

    const topicItems = meta.topics.filter((t) => f.components.has(t.component));
    const years = meta.years.map((y) => ({ value: String(y), label: String(y) }));
    const exams = metas.map((m) => ({ value: m.exam, label: m.label }));

    return h('div', { className: 'dm-row' },
      h('aside', { className: 'dm-cond', 'aria-label': '查询条件' },
        h(E.Select, { label: '考试', options: exams, value: exam, onChange: changeExam }),
        h(Facet, { title: '卷别', items: meta.components, picked: f.components, onChange: setComponents, grid: meta.components.length > 2 }),
        h('section', { style: { display: 'flex', flexDirection: 'column', gap: 8 } },
          h('div', { className: 'fx-head' }, h('span', { className: 'fs-small', style: { fontFamily: 'var(--font-medium)' } }, '年份')),
          h('div', { className: 'years' },
            h(E.Select, { ariaLabel: '起始年份', size: 'sm', options: years, value: String(f.from), onChange: (v) => setF({ ...f, from: +v }) }),
            h('span', null, '至'),
            h(E.Select, { ariaLabel: '结束年份', size: 'sm', options: years, value: String(f.to), onChange: (v) => setF({ ...f, to: +v }) }))),
        topicItems.length ? h(Facet, { title: '主题', items: topicItems, picked: f.topics, onChange: (s) => setF({ ...f, topics: s }) }) : null,
        taskItems.length ? h(Facet, { title: '小问类型', items: taskItems, picked: tasks, onChange: (s) => setF({ ...f, tasks: s }) }) : null),
      h('main', { className: 'dm-results' },
        h('div', { className: 'headline' },
          h('b', null, view.length), h('span', null, '题'), h('b', null, sum(rows)), h('span', null, '分')),
        h('div', { className: 'selbar' },
          h('div', { className: 'dm-meta', style: { flexGrow: 1 } },
            h('span', null, '已选 ', h('b', null, picked.length), ' 题'), h('span', null, h('b', null, sum(picked)), ' 分')),
          h(E.Button, { variant: 'primary', size: 'sm', icon: 'i-plus', disabled: !picked.length, onClick: () => setAdding(true) }, '加入题组')),
        h('div', { className: 'dm-tablebox' },
          allRows.length ? h(E.Table, {
            ariaLabel: '题目', rows: view, selectable: true, selected, onSelectedChange: onSelected, minWidth: 560,
            columns: [
              { key: 'year', label: '年份', kind: 'id', width: 96 },
              { key: 'season', label: '考季', kind: 'text', width: 88, sortValue: (r) => r.month },
              { key: 'paper', label: '卷号', kind: 'id', width: 80 },
              { key: 'qn', label: '题号', kind: 'text', sortValue: (r) => r.q },
              { key: 'parts', label: '小问数', kind: 'number', width: 96 },
              { key: 'marks', label: '分值', kind: 'number', unit: '分', width: 112 },
            ],
          }) : h(E.Loading, { label: '读取题目' }))),
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
      h('div', { style: { padding: '0 24px', display: 'flex', flexDirection: 'column', gap: 12 } },
        d.image_space ? h(E.SegmentedControl, { ariaLabel: '题图', value: crop, onChange: setCrop,
          options: [{ value: 'compact', label: '仅题目' }, { value: 'space', label: '含答题区' }] }) : null,
        img ? h('div', { className: 'qimg' }, h('img', { src: img.src, alt: `${d.code} 第 ${d.q} 题题图` })) : null),
      h('div', { style: { padding: '16px 24px 0' } },
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

  const SOURCE_ICON = { query: 'i-search', paper: 'i-doc', import: 'i-upload', manual: 'i-list' };

  function SetsPage({ sets, current, reloadSets, toast }) {
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
    const create = () => send('POST', '/api/sets', { name: '题组', items: [] })
      .then((n) => { reloadSets(); location.hash = '#/sets/' + n.id; });
    return h('div', { className: 'dm-row' },
      h('aside', { className: 'setlist' },
        h('div', { style: { display: 'flex', gap: 8 } },
          h(E.Button, { variant: 'secondary', size: 'sm', icon: 'i-plus', onClick: create }, '新建题组'),
          h(E.Button, { variant: 'secondary', size: 'sm', icon: 'i-upload', onClick: () => fileRef.current.click() }, '导入 JSON'),
          h('input', { ref: fileRef, type: 'file', accept: '.json,application/json', className: 'hidden-input', onChange: importFile })),
        sets.length ? h(E.List, {
          variant: 'two-line', selectable: true, ariaLabel: '题组', value: s ? s.id : undefined,
          onChange: (v) => { location.hash = '#/sets/' + v; },
          items: sets.map((x) => ({ value: x.id, icon: SOURCE_ICON[x.source] || 'i-list', title: x.name, subtitle: `${x.count} 题 ${x.marks} 分` })),
        }) : h(E.EmptyState, { icon: 'i-list', title: '还没有题组' })),
      s ? h(SetDetail, { key: s.id, s, reloadSets, toast }) : h('main', { className: 'setmain' }));
  }

  function SetDetail({ s, reloadSets, toast }) {
    const [rows, setRows] = useState(null);
    const [selected, setSelected] = useState([]);
    const [renaming, setRenaming] = useState(false);
    const [deleting, setDeleting] = useState(false);
    const [name, setName] = useState(s.name);

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

    return h('main', { className: 'setmain' },
      h('div', { style: { display: 'flex', flexDirection: 'column', gap: 8 } },
        h('div', { style: { display: 'flex', alignItems: 'center', gap: 8 } },
          h('h1', { style: { flexGrow: 1 } }, s.name),
          h(E.Button, { variant: 'secondary', size: 'sm', onClick: () => { setName(s.name); setRenaming(true); } }, '重命名题组'),
          h(E.Button, { variant: 'secondary', size: 'sm', onClick: () => setDeleting(true) }, '删除题组')),
        h('div', { className: 'dm-meta' },
          h('span', null, h('b', null, s.count), ' 题'), h('span', null, h('b', null, s.marks), ' 分'),
          h('span', { className: 't' }, s.created))),
      h('div', { className: 'dm-toolbar' },
        h('span', { className: 'dm-grow' }),
        h(E.IconButton, { icon: 'k-up', label: '上移题目', variant: 'ghost', size: 'sm', tooltip: 'below', disabled: !selected.length, onClick: () => move(-1) }),
        h(E.IconButton, { icon: 'k-down', label: '下移题目', variant: 'ghost', size: 'sm', tooltip: 'below', disabled: !selected.length, onClick: () => move(1) }),
        h(E.IconButton, { icon: 'i-trash', label: '移出题组', variant: 'ghost', size: 'sm', tooltip: 'below', disabled: !selected.length, onClick: remove }),
        h(E.Button, { variant: 'secondary', size: 'sm', onClick: () => { location.href = `/api/sets/${s.id}/export`; } }, '导出 JSON')),
      h('div', { className: 'dm-tablebox' },
        !rows ? h(E.Loading, null) : view.length ? h(E.Table, {
          ariaLabel: '题组中的题目', rows: view, selectable: true, selected, onSelectedChange: setSelected, minWidth: 520,
          columns: [
            { key: 'n', label: '序号', kind: 'id', width: 88 },
            { key: 'year', label: '年份', kind: 'id', width: 80, sortable: false },
            { key: 'season', label: '考季', kind: 'text', width: 80, sortable: false },
            { key: 'paper', label: '卷号', kind: 'id', width: 72, sortable: false },
            { key: 'qn', label: '题号', kind: 'text', sortable: false },
            { key: 'marks', label: '分值', kind: 'number', unit: '分', width: 96, sortable: false },
          ],
        }) : h(E.EmptyState, { icon: 'i-search', title: '题组中还没有题目', description: '在查询页选中题目后加入题组' })),
      renaming ? h(E.Dialog, { open: true, title: '重命名题组', confirmLabel: '保存名称', onClose: () => setRenaming(false),
        onConfirm: () => save({ name }) },
      h(E.TextField, { label: '名称', value: name, onChange: (e) => setName(e.target.value) })) : null,
      deleting ? h(E.Dialog, { open: true, danger: true, title: '删除题组', confirmLabel: '删除题组', onClose: () => setDeleting(false),
        onConfirm: () => send('DELETE', '/api/sets/' + s.id).then(() => { location.hash = '#/sets'; reloadSets(); }) },
      h('p', null, `删除后 ${s.name} 将无法恢复。题库中的题目不受影响。`)) : null);
  }

  // ------------------------------------------------------------------ shell

  function App() {
    const hash = useHash();
    const toast = E.useToast();
    const [metas, setMetas] = useState(null);
    const [sets, setSets] = useState([]);
    const [search, setSearch] = useState('');
    const reloadSets = useCallback(() => api('/api/sets').then(setSets), []);
    useEffect(() => { api('/api/meta').then(setMetas); reloadSets(); }, []);

    const page = hash.split('/')[1] || 'query';
    const nav = [
      { value: 'query', label: '查询', icon: 'i-search', href: '#/query' },
      { value: 'sets', label: '题组', icon: 'i-list', href: '#/sets' },
      { value: 'templates', label: '模板', icon: 'i-doc', href: '#/templates' },
    ];
    const titles = { query: '查询', sets: '题组', templates: '模板', settings: '设置' };
    let body;
    if (!metas) body = h(E.PageLoader || E.Loading, null);
    else if (page === 'sets') body = h(SetsPage, { sets, current: hash.split('/')[2], reloadSets, toast });
    else if (page === 'query') body = h(QueryPage, { metas, search, sets, reloadSets, toast });
    else body = h('div', { className: 'dm-row' }, h(E.EmptyState, { icon: 'i-inbox', title: '下一阶段实现' }));
    return h('div', { className: 'dm-shell' },
      h(E.Sidebar, { name: 'AL 题库', items: nav, value: page, tools: [{ label: '设置', icon: 'i-sliders', onClick: () => { location.hash = '#/settings'; } }] }),
      h('div', { className: 'dm-col' },
        h(E.TopBar, { title: titles[page] || '查询', search: page === 'query' ? '搜索' : undefined, onSearch: setSearch }),
        body));
  }

  ReactDOM.createRoot(document.getElementById('root')).render(h(E.ToastProvider, null, h(App)));
})();
