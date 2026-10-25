import React, { useEffect, useState } from 'react';
import { createRoot } from 'react-dom/client';

const h = React.createElement;
const PAGE_SIZE = 10;

async function fetchJSON(url, options) {
  const response = await fetch(url, options);
  if (!response.ok) throw new Error(`Request failed (${response.status}): ${await response.text()}`);
  return response.json();
}

function App() {
  const [query, setQuery] = useState('');
  const [sort, setSort] = useState('created_desc');
  const [page, setPage] = useState(1);
  const [results, setResults] = useState({ items: [], total: 0 });
  const [actions, setActions] = useState([]);
  const [refresh, setRefresh] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setError('');
    const params = new URLSearchParams({ q: query, page, page_size: PAGE_SIZE, sort });
    fetchJSON(`/notes/search/?${params}`, { signal: controller.signal })
      .then(setResults)
      .catch(error => {
        if (error.name !== 'AbortError') setError(error.message);
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [query, sort, page, refresh]);

  useEffect(() => {
    fetchJSON('/action-items/').then(setActions).catch(error => setError(error.message));
  }, []);

  async function addNote(event) {
    event.preventDefault();
    const form = event.currentTarget;
    const values = new FormData(form);
    try {
      await fetchJSON('/notes/', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title: values.get('title'), content: values.get('content') }),
      });
      form.reset();
      setPage(1);
      setRefresh(value => value + 1);
    } catch (error) { setError(error.message); }
  }

  async function addAction(event) {
    event.preventDefault();
    const form = event.currentTarget;
    try {
      await fetchJSON('/action-items/', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ description: new FormData(form).get('description') }),
      });
      form.reset();
      setActions(await fetchJSON('/action-items/'));
    } catch (error) { setError(error.message); }
  }

  async function completeAction(id) {
    try {
      await fetchJSON(`/action-items/${id}/complete`, { method: 'PUT' });
      setActions(await fetchJSON('/action-items/'));
    } catch (error) { setError(error.message); }
  }

  return h('main', null,
    h('h1', null, 'Modern Software Dev Starter'),
    error && h('p', { role: 'alert' }, error),
    h('section', null,
      h('h2', null, 'Notes'),
      h('form', { id: 'note-form', onSubmit: addNote },
        h('input', { name: 'title', placeholder: 'Title', 'aria-label': 'Note title', required: true }),
        h('input', { name: 'content', placeholder: 'Content', 'aria-label': 'Note content', required: true }),
        h('button', { type: 'submit' }, 'Add')),
      h('div', { className: 'search-controls' },
        h('label', null, 'Search notes', h('input', {
          id: 'note-search', type: 'search', value: query, placeholder: 'Search title or content',
          onChange: event => { setQuery(event.target.value); setPage(1); },
        })),
        h('label', null, 'Sort', h('select', {
          id: 'note-sort', value: sort,
          onChange: event => { setSort(event.target.value); setPage(1); },
        }, h('option', { value: 'created_desc' }, 'Newest first'),
        h('option', { value: 'title_asc' }, 'Title A–Z')))),
      h('p', { id: 'result-count', role: 'status' }, loading ? 'Loading notes…' : `${results.total} result${results.total === 1 ? '' : 's'}`),
      h('ul', { id: 'notes', 'aria-busy': loading }, results.items.map(note =>
        h('li', { key: note.id }, `${note.title}: ${note.content}`))),
      !loading && results.total === 0 && h('p', null, 'No notes found.'),
      h('nav', { className: 'pagination', 'aria-label': 'Notes pagination' },
        h('button', { id: 'previous-page', disabled: loading || page === 1, onClick: () => setPage(page - 1) }, 'Previous'),
        h('span', { id: 'page-number' }, `Page ${page} of ${Math.max(1, Math.ceil(results.total / PAGE_SIZE))}`),
        h('button', { id: 'next-page', disabled: loading || page * PAGE_SIZE >= results.total, onClick: () => setPage(page + 1) }, 'Next'))),
    h('section', null,
      h('h2', null, 'Action Items'),
      h('form', { id: 'action-form', onSubmit: addAction },
        h('input', { name: 'description', placeholder: 'Description', 'aria-label': 'Action description', required: true }),
        h('button', { type: 'submit' }, 'Add')),
      h('ul', { id: 'actions' }, actions.map(action => h('li', { key: action.id },
        `${action.description} [${action.completed ? 'done' : 'open'}]`,
        !action.completed && h('button', { onClick: () => completeAction(action.id) }, 'Complete'))))));
}

createRoot(document.getElementById('root')).render(h(App));
