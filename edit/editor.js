const OWNER = 'itayoriel';
const REPO = 'hilagalant';
const BRANCH = 'main';
const API = `https://api.github.com/repos/${OWNER}/${REPO}`;
const TOKEN_KEY = 'hg_editor_token';
const PART_SIZE = 40 * 1024 * 1024;
const MAX_PHOTO = 90 * 1024 * 1024;

const $ = (sel) => document.querySelector(sel);
const statusEl = $('#ed-status');
const progressEl = $('#ed-progress');
const saveBtn = $('#ed-save');
const videosEl = $('#ed-videos');
const stillsEl = $('#ed-stills');

let token = readToken();
let site = {};
let dirty = false;
let saving = false;

function readToken() {
  try { return localStorage.getItem(TOKEN_KEY) || ''; } catch { return ''; }
}
function storeToken(value) {
  try { value ? localStorage.setItem(TOKEN_KEY, value) : localStorage.removeItem(TOKEN_KEY); } catch {}
}

function setStatus(text, progress) {
  statusEl.textContent = text || '';
  if (progress == null) {
    progressEl.hidden = true;
  } else {
    progressEl.hidden = false;
    progressEl.firstElementChild.style.width = `${Math.round(progress * 100)}%`;
  }
}

function markDirty() {
  if (saving) return;
  dirty = true;
  saveBtn.disabled = false;
  setStatus('Unsaved changes');
}

window.addEventListener('beforeunload', (e) => {
  if (dirty || saving) { e.preventDefault(); e.returnValue = ''; }
});

async function gh(path, opts = {}) {
  const res = await fetch(API + path, {
    ...opts,
    cache: 'no-store',
    headers: {
      Authorization: `Bearer ${token}`,
      Accept: 'application/vnd.github+json',
      'X-GitHub-Api-Version': '2022-11-28',
      ...(opts.body ? { 'Content-Type': 'application/json' } : {}),
    },
  });
  if (!res.ok) {
    const err = new Error(`GitHub ${res.status}`);
    err.status = res.status;
    err.detail = await res.text();
    throw err;
  }
  return res.status === 204 ? null : res.json();
}

function encodePath(path) {
  return path.split('/').map(encodeURIComponent).join('/');
}

function decodeBase64Utf8(b64) {
  const bin = atob(b64.replace(/\s/g, ''));
  return new TextDecoder().decode(Uint8Array.from(bin, (c) => c.charCodeAt(0)));
}

async function readRepoText(path) {
  try {
    const file = await gh(`/contents/${encodePath(path)}?ref=${BRANCH}`);
    return decodeBase64Utf8(file.content);
  } catch (e) {
    if (e.status === 404) return null;
    throw e;
  }
}

function slugify(s) {
  return s.trim().toLowerCase()
    .replace(/[_\s]+/g, '-')
    .replace(/[^a-z0-9-]/g, '')
    .replace(/-+/g, '-')
    .replace(/^-|-$/g, '');
}

function titleize(s) {
  return s.split(/[_\-\s]+/).filter(Boolean)
    .map((w) => w[0].toUpperCase() + w.slice(1).toLowerCase())
    .join(' ');
}

function stem(filename) {
  return filename.replace(/\.[^.]+$/, '');
}

function ext(filename) {
  const m = filename.match(/\.([^.]+)$/);
  return m ? m[1].toLowerCase() : '';
}

function lines(text) {
  return (text || '').split('\n').map((l) => l.trim()).filter(Boolean);
}

function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text != null) node.textContent = text;
  return node;
}

function makeEditable(node, singleLine) {
  node.contentEditable = 'true';
  node.spellcheck = false;
  node.classList.add('ed-editable');
  node.addEventListener('input', markDirty);
  node.addEventListener('paste', (e) => {
    e.preventDefault();
    const text = e.clipboardData.getData('text/plain');
    document.execCommand('insertText', false, singleLine ? text.replace(/\s*\n\s*/g, ' ') : text);
  });
  if (singleLine) {
    node.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') { e.preventDefault(); node.blur(); }
    });
  }
}

function removeButton(target) {
  const btn = el('button', 'ed-remove', '✕');
  btn.type = 'button';
  btn.title = 'Remove';
  btn.addEventListener('click', (e) => {
    e.stopPropagation();
    const removed = target.classList.toggle('ed-removed');
    btn.textContent = removed ? '↺' : '✕';
    btn.title = removed ? 'Bring back' : 'Remove';
    markDirty();
  });
  return btn;
}

function videoEntry({ slug, mods, title, file }) {
  const entry = el('div', ['gallery-entry', 'ed-entry', ...mods].join(' '));
  entry._data = { slug, mods, file: file || null };

  const titleEl = el('p', 'video-title', title);
  makeEditable(titleEl, true);

  const box = el('div', 'gallery-item');
  if (file) {
    const video = el('video', 'ed-preview');
    video.muted = true;
    video.playsInline = true;
    video.preload = 'metadata';
    video.src = URL.createObjectURL(file);
    video.addEventListener('loadedmetadata', () => {
      if (video.videoHeight > video.videoWidth) box.classList.add('portrait');
    });
    box.append(video, el('span', 'ed-badge', 'New'));
  } else {
    const img = el('img', 'v-thumb');
    img.alt = '';
    img.addEventListener('load', () => {
      if (img.naturalHeight > img.naturalWidth) box.classList.add('portrait');
    });
    img.src = `/assets/gallery/${slug}.jpg`;
    box.append(img);
  }
  box.append(removeButton(entry));
  entry.append(titleEl, box);
  return entry;
}

function stillEntry({ name, file }) {
  const wrap = el('div', 'ed-still');
  wrap._data = { name, file: file || null };
  const img = el('img', 'still');
  img.alt = '';
  img.src = file ? URL.createObjectURL(file) : `/assets/stills/${name}`;
  wrap.append(img);
  if (file) wrap.append(el('span', 'ed-badge', 'New'));
  wrap.append(removeButton(wrap));
  return wrap;
}

function renderText() {
  const rolesEl = $('#ed-roles');
  rolesEl.innerHTML = '';
  (site.roles || []).forEach((role) => {
    const p = el('p', 'role', role);
    makeEditable(p, true);
    rolesEl.append(p);
  });

  const tagline = $('#ed-tagline');
  tagline.textContent = site.tagline || '';
  makeEditable(tagline, true);

  const about = $('#ed-about');
  about.innerText = (site.about || []).join('\n');
  makeEditable(about, false);
}

function renderMedia(videoLines, stillLines) {
  videosEl.querySelectorAll('.ed-entry').forEach((n) => n.remove());
  stillsEl.innerHTML = '';
  const titles = site.titles || {};

  videoLines.forEach((line) => {
    const [slug, ...mods] = line.split(',').map((p) => p.trim());
    videosEl.append(videoEntry({ slug, mods: mods.filter(Boolean), title: titles[slug] || titleize(slug) }));
  });
  stillLines.forEach((name) => stillsEl.append(stillEntry({ name })));

  const sortOpts = {
    animation: 180,
    filter: '.ed-editable, .ed-remove',
    preventOnFilter: false,
    onEnd: markDirty,
  };
  Sortable.create(videosEl, { ...sortOpts, draggable: '.ed-entry' });
  Sortable.create(stillsEl, { ...sortOpts, draggable: '.ed-still' });
}

function usedVideoSlugs() {
  return new Set([...videosEl.querySelectorAll('.ed-entry')].map((n) => n._data.slug));
}

$('#ed-add-video').addEventListener('change', (e) => {
  const taken = usedVideoSlugs();
  for (const file of e.target.files) {
    const base = slugify(stem(file.name)) || `video-${Date.now()}`;
    let slug = base;
    for (let i = 2; taken.has(slug); i++) slug = `${base}-${i}`;
    taken.add(slug);
    const entry = videoEntry({ slug, mods: [], title: titleize(stem(file.name)) || 'New Video', file });
    videosEl.append(entry);
  }
  e.target.value = '';
  markDirty();
  videosEl.lastElementChild?.scrollIntoView({ behavior: 'smooth', block: 'center' });
});

$('#ed-add-photo').addEventListener('change', (e) => {
  let i = 0;
  for (const file of e.target.files) {
    const name = `photo-${Date.now()}-${i++}.jpg`;
    stillsEl.append(stillEntry({ name, file }));
  }
  e.target.value = '';
  markDirty();
  stillsEl.lastElementChild?.scrollIntoView({ behavior: 'smooth', block: 'center' });
});

function blobToBase64(blob) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result.slice(reader.result.indexOf(',') + 1));
    reader.onerror = () => reject(reader.error);
    reader.readAsDataURL(blob);
  });
}

async function uploadBlob(blob) {
  const content = await blobToBase64(blob);
  const res = await gh('/git/blobs', { method: 'POST', body: JSON.stringify({ content, encoding: 'base64' }) });
  return res.sha;
}

async function commitChanges(textFiles, blobEntries, deletePaths, message) {
  for (let attempt = 0; attempt < 3; attempt++) {
    const ref = await gh(`/git/ref/heads/${BRANCH}`);
    const head = await gh(`/git/commits/${ref.object.sha}`);
    const current = await gh(`/git/trees/${head.tree.sha}?recursive=1`);
    const existing = new Set(current.tree.map((t) => t.path));

    const tree = [
      ...Object.entries(textFiles).map(([path, content]) => ({ path, mode: '100644', type: 'blob', content })),
      ...blobEntries.map(({ path, sha }) => ({ path, mode: '100644', type: 'blob', sha })),
      ...deletePaths.filter((p) => existing.has(p)).map((path) => ({ path, mode: '100644', type: 'blob', sha: null })),
    ];

    const newTree = await gh('/git/trees', { method: 'POST', body: JSON.stringify({ base_tree: head.tree.sha, tree }) });
    const commit = await gh('/git/commits', {
      method: 'POST',
      body: JSON.stringify({ message, tree: newTree.sha, parents: [head.sha] }),
    });
    try {
      await gh(`/git/refs/heads/${BRANCH}`, { method: 'PATCH', body: JSON.stringify({ sha: commit.sha }) });
      return;
    } catch (e) {
      if (e.status !== 422 || attempt === 2) throw e;
    }
  }
}

function collect() {
  const videoOrder = [];
  const titles = {};
  const uploads = [];
  const deletions = [];

  videosEl.querySelectorAll('.ed-entry').forEach((entry) => {
    const { slug, mods, file } = entry._data;
    if (entry.classList.contains('ed-removed')) {
      if (!file) deletions.push(`assets/gallery/${slug}.mp4`, `assets/gallery/${slug}.jpg`);
      return;
    }
    videoOrder.push([slug, ...mods].join(','));
    titles[slug] = entry.querySelector('.video-title').textContent.trim() || titleize(slug);
    if (file) uploads.push({ kind: 'video', slug, file });
  });

  const stillOrder = [];
  stillsEl.querySelectorAll('.ed-still').forEach((wrap) => {
    const { name, file } = wrap._data;
    if (wrap.classList.contains('ed-removed')) {
      if (!file) deletions.push(`assets/stills/${name}`);
      return;
    }
    stillOrder.push(name);
    if (file) uploads.push({ kind: 'photo', name, file });
  });

  const roles = [...document.querySelectorAll('#ed-roles .role')].map((p) => p.textContent.trim()).filter(Boolean);
  const newSite = {
    ...site,
    roles,
    tagline: $('#ed-tagline').textContent.trim(),
    about: lines($('#ed-about').innerText),
    titles,
  };

  return { videoOrder, stillOrder, newSite, uploads, deletions };
}

// Pieces go to a throwaway upload-* branch so raw files never enter main's history.
async function uploadVideos(videos, totalBytes) {
  const parts = [];
  let sent = 0;
  for (let v = 0; v < videos.length; v++) {
    const { slug, file } = videos[v];
    const dir = `uploads/${slug}.${ext(file.name) || 'mp4'}`;
    const count = Math.ceil(file.size / PART_SIZE);
    for (let p = 0; p < count; p++) {
      const chunk = file.slice(p * PART_SIZE, (p + 1) * PART_SIZE);
      setStatus(`Uploading video ${v + 1} of ${videos.length}…`, sent / totalBytes);
      parts.push({ path: `${dir}/part-${String(p).padStart(3, '0')}`, sha: await uploadBlob(chunk) });
      sent += chunk.size;
    }
  }
  setStatus('Sending videos for processing…', 1);
  const ref = await gh(`/git/ref/heads/${BRANCH}`);
  const head = await gh(`/git/commits/${ref.object.sha}`);
  // Built on main's tree: GitHub only runs workflows present in the pushed branch itself.
  const tree = await gh('/git/trees', {
    method: 'POST',
    body: JSON.stringify({
      base_tree: head.tree.sha,
      tree: parts.map(({ path, sha }) => ({ path, mode: '100644', type: 'blob', sha })),
    }),
  });
  const commit = await gh('/git/commits', {
    method: 'POST',
    body: JSON.stringify({ message: 'Video upload from editor', tree: tree.sha, parents: [ref.object.sha] }),
  });
  await gh('/git/refs', {
    method: 'POST',
    body: JSON.stringify({ ref: `refs/heads/upload-${Date.now()}`, sha: commit.sha }),
  });
}

async function uploadPhotos(photos) {
  const entries = [];
  for (let i = 0; i < photos.length; i++) {
    const { name, file } = photos[i];
    if (file.size > MAX_PHOTO) throw new Error(`"${file.name}" is too large for a photo (over 90MB).`);
    setStatus(`Uploading photo ${i + 1} of ${photos.length}…`, i / photos.length);
    const base = name.replace(/\.jpg$/, '');
    entries.push({ path: `assets/incoming/stills/${base}.${ext(file.name) || 'jpg'}`, sha: await uploadBlob(file) });
  }
  return entries;
}

saveBtn.addEventListener('click', async () => {
  if (saving) return;
  saving = true;
  saveBtn.disabled = true;
  document.body.classList.add('ed-saving');
  try {
    const { videoOrder, stillOrder, newSite, uploads, deletions } = collect();
    const videos = uploads.filter((u) => u.kind === 'video');
    const photos = uploads.filter((u) => u.kind === 'photo');

    if (videos.length) await uploadVideos(videos, videos.reduce((n, v) => n + v.file.size, 0));
    const blobEntries = await uploadPhotos(photos);

    setStatus('Saving…', null);
    const textFiles = {
      'order/videos.txt': videoOrder.join('\n') + '\n',
      'order/stills.txt': stillOrder.join('\n') + '\n',
      'content/site.json': JSON.stringify(newSite, null, 2) + '\n',
    };
    await commitChanges(textFiles, blobEntries, deletions, 'Update site from editor');

    site = newSite;
    videosEl.querySelectorAll('.ed-entry.ed-removed').forEach((n) => n.remove());
    stillsEl.querySelectorAll('.ed-still.ed-removed').forEach((n) => n.remove());
    document.querySelectorAll('.ed-entry, .ed-still').forEach((n) => { n._data.file = null; });
    document.querySelectorAll('.ed-badge').forEach((n) => n.remove());

    dirty = false;
    setStatus(uploads.length
      ? 'Saved ✓ New videos/photos will appear on the site in a few minutes (you can close this page)'
      : 'Saved ✓ The site will update in about a minute');
  } catch (err) {
    console.error(err);
    if (err.status === 401 || err.status === 403) {
      setStatus('Your access key was rejected. Reload the page to enter it again.');
      storeToken('');
    } else {
      setStatus(`Couldn't save: ${err.message}. Nothing was changed — try again.`);
    }
    saveBtn.disabled = false;
  } finally {
    saving = false;
    document.body.classList.remove('ed-saving');
  }
});

async function verifyToken(candidate) {
  const prev = token;
  token = candidate;
  try {
    const repo = await gh('');
    if (!repo.permissions || !repo.permissions.push) throw new Error('This key can view but not edit the site.');
    return true;
  } catch (e) {
    token = prev;
    throw e.status === 401 || e.status === 404 ? new Error("That access key didn't work.") : e;
  }
}

async function start() {
  setStatus('Loading…');
  try {
    const [videosTxt, stillsTxt, siteTxt] = await Promise.all([
      readRepoText('order/videos.txt'),
      readRepoText('order/stills.txt'),
      readRepoText('content/site.json'),
    ]);
    site = siteTxt ? JSON.parse(siteTxt) : { roles: [], tagline: '', about: [], titles: {} };
    renderText();
    renderMedia(lines(videosTxt), lines(stillsTxt));
    $('#ed-page').hidden = false;
    setStatus('');
  } catch (err) {
    console.error(err);
    if (err.status === 401) {
      storeToken('');
      showLogin("Your access key has expired. Please enter a new one.");
    } else {
      setStatus(`Couldn't load the site: ${err.message}`);
    }
  }
}

function showLogin(message) {
  $('#ed-login').hidden = false;
  $('#ed-login-error').textContent = message || '';
  $('#ed-token').focus();
}

$('#ed-login-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  const value = $('#ed-token').value.trim();
  $('#ed-login-error').textContent = '';
  try {
    await verifyToken(value);
    storeToken(value);
    $('#ed-login').hidden = true;
    start();
  } catch (err) {
    $('#ed-login-error').textContent = err.message;
  }
});

if (token) start(); else showLogin();
