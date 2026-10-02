/* 题库数据管理 (docs/data-manager.md). React without a build step: h = createElement.
   Pages: #/query, #/sets/<id>[/paper | /export/<template>], #/templates/<id>, #/settings. */
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
            ariaLabel: '题目', rows: view, selectable: true, selected, onSelectedChange: onSelected, minWidth: 460,
            columns: [
              { key: 'year', label: '年份', kind: 'id', width: 88 },
              { key: 'season', label: '考季', kind: 'text', width: 72, sortValue: (r) => r.month },
              { key: 'paper', label: '卷号', kind: 'id', width: 64 },
              { key: 'qn', label: '题号', kind: 'text', sortValue: (r) => r.q },
              { key: 'parts', label: '小问数', kind: 'number', width: 88 },
              { key: 'marks', label: '分值', kind: 'number', unit: '分', width: 88 },
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

  function SetsPage({ sets, current, reloadSets, templates, toast }) {
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
      s ? h(SetDetail, { key: s.id, s, reloadSets, templates, toast }) : h('main', { className: 'setmain' }));
  }

  function SetDetail({ s, reloadSets, templates, toast }) {
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

    return h(React.Fragment, null, h('main', { className: 'setmain' },
      h('div', { style: { display: 'flex', flexDirection: 'column', gap: 8 } },
        h('h1', null, s.name),
        h('div', { className: 'dm-meta' },
          h('span', null, h('b', null, s.count), ' 题'), h('span', null, h('b', null, s.marks), ' 分'),
          h('span', { className: 't' }, s.created))),
      h('div', { className: 'dm-toolbar' },
        h(E.Button, { variant: 'secondary', size: 'sm', onClick: () => { setName(s.name); setRenaming(true); } }, '重命名题组'),
        h(E.Button, { variant: 'secondary', size: 'sm', onClick: () => setDeleting(true) }, '删除题组'),
        h('span', { className: 'dm-grow' }),
        h(E.IconButton, { icon: 'k-up', label: '上移题目', variant: 'ghost', size: 'sm', tooltip: 'below', disabled: !selected.length, onClick: () => move(-1) }),
        h(E.IconButton, { icon: 'k-down', label: '下移题目', variant: 'ghost', size: 'sm', tooltip: 'below', disabled: !selected.length, onClick: () => move(1) }),
        h(E.IconButton, { icon: 'i-trash', label: '移出题组', variant: 'ghost', size: 'sm', tooltip: 'below', disabled: !selected.length, onClick: remove }),
        h(E.Button, { variant: 'secondary', size: 'sm', onClick: () => { location.href = `/api/sets/${s.id}/export`; } }, '导出 JSON')),
      h('div', { className: 'dm-tablebox' },
        !rows ? h(E.Loading, null) : view.length ? h(E.Table, {
          ariaLabel: '题组中的题目', rows: view, selectable: true, selected, onSelectedChange: setSelected, minWidth: 440,
          columns: [
            { key: 'n', label: '序号', kind: 'id', width: 80 },
            { key: 'year', label: '年份', kind: 'id', width: 72, sortable: false },
            { key: 'season', label: '考季', kind: 'text', width: 72, sortable: false },
            { key: 'paper', label: '卷号', kind: 'id', width: 64, sortable: false },
            { key: 'qn', label: '题号', kind: 'text', sortable: false },
            { key: 'marks', label: '分值', kind: 'number', unit: '分', width: 80, sortable: false },
          ],
        }) : h(E.EmptyState, { icon: 'i-search', title: '题组中还没有题目', description: '在查询页选中题目后加入题组' })),
      renaming ? h(E.Dialog, { open: true, title: '重命名题组', confirmLabel: '保存名称', onClose: () => setRenaming(false),
        onConfirm: () => save({ name }) },
      h(E.TextField, { label: '名称', value: name, onChange: (e) => setName(e.target.value) })) : null,
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
      h(E.IconButton, { icon: 'i-doc', label: '下载' + label, variant: 'ghost', size: 'sm', disabled: !n, onClick: () => download(`/doc/${s.id}/${kind}?download=1`) }),
      h(E.IconButton, { icon: 'i-arrow-r', label: '打开' + label, variant: 'ghost', size: 'sm', disabled: !n, onClick: () => open(`/doc/${s.id}/${kind}`, '_blank') }));
    return h('aside', { className: 'setpanel' },
      h('section', null,
        h('div', { className: 'panel-row' },
          h('h2', { className: 'fs-lead', style: { margin: 0, flexGrow: 1 } }, '题目卷'),
          pages != null ? h('span', { className: 'dm-meta' }, h('span', null, h('b', null, pages), ' 页')) : null,
          h(E.IconButton, { icon: 'i-arrow-r', label: '打开题目卷', variant: 'ghost', size: 'sm', disabled: !s.count, onClick: () => { location.hash = `#/sets/${s.id}/paper`; } })),
        h('div', { style: { display: 'flex', gap: 8 } },
          h(E.Button, { variant: 'primary', size: 'sm', icon: 'i-doc', disabled: !s.count || pages == null, onClick: () => download(`/api/sets/${s.id}/paper.pdf`) }, '下载 PDF'),
          h(E.Button, { variant: 'secondary', size: 'sm', disabled: !s.count || pages == null, onClick: openBoard }, '打开白板')),
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
        h('h2', { className: 'fs-lead', style: { margin: '0 0 8px' } }, '评分细则与详解'),
        docRow('评分细则', 'scheme', s.docs.scheme),
        docRow('详解', 'explanation', s.docs.explanation)),
      h('section', null,
        h('div', { className: 'panel-row' },
          h('h2', { className: 'fs-lead', style: { margin: 0, flexGrow: 1 } }, '导出'),
          h(E.IconButton, { icon: 'i-sliders', label: '打开导出页', variant: 'ghost', size: 'sm', tooltip: 'below', onClick: () => { location.hash = `#/sets/${s.id}/export/${tid}`; } })),
        h(E.Select, { label: '模板', size: 'sm', options: templates.map((t) => ({ value: t.id, label: t.name })), value: tid, onChange: setTid }),
        h('div', null, h(E.Button, { variant: 'primary', size: 'sm', icon: 'i-box', disabled: !s.count, onClick: () => downloadZip(s, { template: tid }, toast) }, '下载 ZIP'))));
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
        h('div', { style: { flexGrow: 1, display: 'flex', flexDirection: 'column', gap: 8 } },
          h('h1', { className: 'fs-h3', style: { margin: 0 } }, s.name),
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

  function ExportPage({ s, tid, templates, reloadTemplates, toast }) {
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
      h('aside', { className: 'ex-side' },
        h('div', { style: { display: 'flex', flexDirection: 'column', gap: 8 } },
          h('h1', { className: 'fs-h3', style: { margin: 0 } }, s.name),
          h('div', { className: 'dm-meta' }, h('span', null, h('b', null, s.count), ' 题'), h('span', null, h('b', null, s.marks), ' 分'))),
        h(E.Select, { label: '模板', options: templates.map((t) => ({ value: t.id, label: t.name })), value: pick, onChange: setPick }),
        st ? h(ExportOptions, { settings: st, onChange: setSt }) : null,
        h('div', { style: { flexGrow: 1 } }),
        h('div', { style: { display: 'flex', gap: 8, flexWrap: 'wrap' } },
          h(E.Button, { variant: 'primary', size: 'md', icon: 'i-box', disabled: !st || !s.count, onClick: () => downloadZip(s, { settings: st, body }, toast) }, '下载 ZIP'),
          h(E.Button, { variant: 'secondary', size: 'md', disabled: !st, onClick: () => { setName(''); setSaving(true); } }, '另存为模板'))),
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
          h(E.IconButton, { icon: 'i-copy', label: '复制 README', variant: 'ghost', size: 'sm', tooltip: 'below', disabled: !pv, onClick: copy })),
        h('div', { className: 'ex-docbody' },
          !pv ? h(E.Loading, null) : doc === 'readme' ? h(MdView, { text: pv.readme }) : h('pre', { className: 'md-code' }, pv.manifest))),
      saving ? h(E.Dialog, { open: true, title: '另存为模板', confirmLabel: '保存模板', onClose: () => setSaving(false), onConfirm: saveAs },
        h(E.TextField, { label: '名称', value: name, onChange: (e) => setName(e.target.value) })) : null);
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
    const [sid, setSid] = useState(sets[0] ? sets[0].id : '');
    const [deleting, setDeleting] = useState(false);
    const area = useRef(null);
    useEffect(() => { if (t) { setName(t.name); setSt(t.settings); setBody(t.body); } }, [t && t.id, templates]);
    useEffect(() => { if (!sid && sets[0]) setSid(sets[0].id); }, [sets.length]);
    const pv = usePreview(tab === 'preview' ? sets.find((x) => x.id === sid) : null, st, body);
    if (!t || !st) return h('div', { className: 'dm-row' }, h(E.Loading, null));
    const changed = name !== t.name || body !== t.body || JSON.stringify(st) !== JSON.stringify(t.settings);
    const go = (id) => { location.hash = '#/templates/' + id; };
    const create = () => send('POST', '/api/templates', { name: '导出模板', settings: templates[0].settings, body: templates[0].body })
      .then((n) => reloadTemplates().then(() => go(n.id)));
    const copy = () => send('POST', '/api/templates', { name, settings: st, body }).then((n) => reloadTemplates().then(() => go(n.id)));
    const save = () => send('PUT', '/api/templates/' + t.id, { name, settings: st, body })
      .then(() => { toast('success', '模板已保存'); return reloadTemplates(); }).catch((e) => toast('error', e.message));
    const insert = (v) => {
      const el = area.current;
      const a = el ? el.selectionStart : body.length;
      const b = el ? el.selectionEnd : body.length;
      setBody(body.slice(0, a) + v + body.slice(b));
      requestAnimationFrame(() => { if (el) { el.focus(); el.selectionStart = el.selectionEnd = a + v.length; } });
    };
    return h('div', { className: 'dm-row tplpage' },
      h('aside', { className: 'tpl-list' },
        h(E.List, { variant: 'compact', selectable: true, ariaLabel: '导出模板', value: t.id, onChange: go,
          items: templates.map((x) => ({ value: x.id, title: x.name })) }),
        h('div', { style: { flexGrow: 1 } }),
        h('div', null, h(E.Button, { variant: 'secondary', size: 'sm', icon: 'i-plus', onClick: create }, '新建导出模板'))),
      h('section', { className: 'tpl-opts' },
        h(E.TextField, { label: '名称', value: name, disabled: t.builtin, onChange: (e) => setName(e.target.value) }),
        h('div', { className: t.builtin ? 'opts locked' : 'opts' }, h(ExportOptions, { settings: st, onChange: t.builtin ? () => {} : setSt })),
        h('div', { style: { flexGrow: 1 } }),
        h('div', { style: { display: 'flex', gap: 8, alignItems: 'center' } },
          h(E.Button, { variant: 'primary', size: 'sm', disabled: t.builtin || !changed, onClick: save }, '保存模板'),
          h(E.Button, { variant: 'secondary', size: 'sm', onClick: copy }, '复制模板'),
          h('span', { className: 'dm-grow' }),
          t.builtin ? null : h(E.IconButton, { icon: 'i-trash', label: '删除模板', variant: 'ghost', size: 'sm', tooltip: 'above', onClick: () => setDeleting(true) }))),
      h('section', { className: 'tpl-edit' },
        h('div', { className: 'panel-row', style: { gap: 24 } },
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
    const [templates, setTemplates] = useState([]);
    const reloadSets = useCallback(() => api('/api/sets').then(setSets), []);
    const reloadTemplates = useCallback(() => api('/api/templates').then(setTemplates), []);
    useEffect(() => { api('/api/meta').then(setMetas); reloadSets(); reloadTemplates(); api('/api/settings').then((o) => applyTheme(o.theme)); }, []);

    const page = hash.split('/')[1] || 'query';
    const nav = [
      { value: 'query', label: '查询', icon: 'i-search', href: '#/query' },
      { value: 'sets', label: '题组', icon: 'i-list', href: '#/sets' },
      { value: 'templates', label: '模板', icon: 'i-doc', href: '#/templates' },
    ];
    const titles = { query: '查询', sets: '题组', templates: '模板', settings: '设置' };
    const [, , arg, sub, subArg] = hash.split('/');
    const cur = page === 'sets' ? sets.find((x) => x.id === arg) : null;
    let body;
    if (!metas) body = h(E.PageLoader || E.Loading, null);
    else if (page === 'sets' && sub === 'paper') {
      body = cur ? h('div', { className: 'dm-row' }, h(PaperPage, { s: cur })) : h(E.Loading, null);
    } else if (page === 'sets' && sub === 'export') {
      body = cur && templates.length ? h(ExportPage, { key: cur.id, s: cur, tid: subArg, templates, reloadTemplates, toast }) : h(E.Loading, null);
    } else if (page === 'sets') body = h(SetsPage, { sets, current: arg, reloadSets, templates, toast });
    else if (page === 'templates') {
      body = templates.length ? h(TemplatesPage, { templates, current: arg, reloadTemplates, sets, toast }) : h(E.Loading, null);
    } else if (page === 'settings') body = h('div', { className: 'dm-row' }, h(SettingsPage));
    else if (page === 'query') body = h(QueryPage, { metas, search, sets, reloadSets, toast });
    else body = h('div', { className: 'dm-row' }, h(E.EmptyState, { icon: 'i-inbox', title: '下一阶段实现' }));
    return h('div', { className: 'dm-shell' },
      h(E.Sidebar, { name: 'AL 题库', items: nav, value: page, tools: [{ label: '设置', icon: 'i-sliders', onClick: () => { location.hash = '#/settings'; } }] }),
      h('div', { className: 'dm-col' },
        h(E.TopBar, {
          title: sub === 'paper' ? '题目卷' : sub === 'export' ? '导出' : (titles[page] || '查询'),
          crumbs: page === 'sets' && (sub === 'paper' || sub === 'export') && cur
            ? [{ label: '题组', href: '#/sets/' + arg }, { label: cur.name, href: '#/sets/' + arg }, { label: sub === 'paper' ? '题目卷' : '导出' }] : undefined,
          search: page === 'query' ? '搜索' : undefined, onSearch: setSearch }),
        body));
  }

  ReactDOM.createRoot(document.getElementById('root')).render(h(E.ToastProvider, null, h(App)));
})();
