/* ==== ДВИЖОК ЗАПИСИ (общий для всех трёх вариантов) ==== */
const RU_DOW  = ['вс','пн','вт','ср','чт','пт','сб'];
const RU_MON  = ['января','февраля','марта','апреля','мая','июня','июля','августа','сентября','октября','ноября','декабря'];
const SLOTS   = ['09:00','10:30','12:00','13:30','15:00','16:30','18:00'];
const DAYOFF  = [0];                 /* 0 = воскресенье выходной */
const DAYS_AHEAD = 14;
const KEY = 'shug_slots_v1';

let store = {};
try { store = JSON.parse(localStorage.getItem(KEY) || '{}'); } catch (e) { store = {}; }

const today = new Date(); today.setHours(0,0,0,0);
const iso = d => d.getFullYear() + '-' + String(d.getMonth()+1).padStart(2,'0') + '-' + String(d.getDate()).padStart(2,'0');
const human = d => d.getDate() + ' ' + RU_MON[d.getMonth()];

function fnv(s){ let h = 2166136261; for (let i=0;i<s.length;i++){ h ^= s.charCodeAt(i); h = Math.imul(h,16777619); } return h>>>0; }
/* демо-занятость: детерминированная, чтобы календарь всегда выглядел «живым» */
function baseBusy(date, slot){ return fnv(date + '|' + slot) % 100 < 38; }
function isBusy(date, slot){
  const ov = store[date];
  if (ov && Object.prototype.hasOwnProperty.call(ov, slot)) return !!ov[slot];
  return baseBusy(date, slot);
}
function setBusy(date, slot, v){
  (store[date] = store[date] || {})[slot] = v;
  try { localStorage.setItem(KEY, JSON.stringify(store)); } catch (e) {}
}
function isPast(date, slot){
  const [h,m] = slot.split(':').map(Number);
  const dt = new Date(date + 'T00:00:00'); dt.setHours(h,m,0,0);
  return dt.getTime() < Date.now();
}
function dayOff(d){ return DAYOFF.indexOf(d.getDay()) > -1; }
function freeCount(d){
  if (dayOff(d)) return 0;
  const k = iso(d);
  return SLOTS.filter(s => !isBusy(k,s) && !isPast(k,s)).length;
}

let days = [];
for (let i=0;i<DAYS_AHEAD;i++){ const d = new Date(today); d.setDate(today.getDate()+i); days.push(d); }
let active = days.find(d => freeCount(d) > 0) || days[0];
let master = new URLSearchParams(location.search).has('master');

const $ = s => document.querySelector(s);

function renderDays(){
  $('#dayStrip').innerHTML = days.map(d => {
    const k = iso(d), n = freeCount(d), off = dayOff(d);
    return '<button class="day' + (k===iso(active)?' on':'') + (off?' off':'') + (!off&&n===0?' full':'') + '" data-d="' + k + '" aria-pressed="' + (k===iso(active)) + '">'
      + '<span class="dow">' + RU_DOW[d.getDay()] + '</span>'
      + '<span class="num">' + d.getDate() + '</span>'
      + '<span class="mark">' + (off ? 'вых' : (n ? n + ' окн.' : 'занят')) + '</span></button>';
  }).join('');
  $('#dayStrip').querySelectorAll('.day').forEach(b => b.addEventListener('click', () => {
    active = days.find(d => iso(d) === b.dataset.d); renderDays(); renderSlots();
  }));
}

function renderSlots(){
  const k = iso(active);
  $('#dayTitle').textContent = RU_DOW[active.getDay()].toUpperCase() + ', ' + human(active);
  const box = $('#slotGrid');
  if (dayOff(active)){
    box.innerHTML = '<p class="cal-empty">Воскресенье — выходной. Выберите другой день.</p>';
    return;
  }
  box.innerHTML = SLOTS.map(s => {
    const past = isPast(k,s), busy = isBusy(k,s);
    const st = past ? 'past' : (busy ? 'busy' : 'free');
    const lbl = past ? 'прошло' : (busy ? 'занято' : 'свободно');
    const sel = chosen && chosen.date === k && chosen.slot === s ? ' sel' : '';
    return '<button class="slot ' + st + sel + '" data-s="' + s + '"' + (past && !master ? ' disabled' : '') + '>'
      + '<b>' + s + '</b><i>' + lbl + '</i></button>';
  }).join('');
  box.querySelectorAll('.slot').forEach(b => b.addEventListener('click', () => {
    const s = b.dataset.s;
    if (master){ setBusy(k, s, !isBusy(k,s)); renderDays(); renderSlots(); return; }
    if (isBusy(k,s) || isPast(k,s)) { toast('Это время занято — выберите соседнее окно'); return; }
    pick(k, s);
  }));
  $('#nextFree').textContent = nextFreeText();
}

function nextFreeText(){
  for (const d of days){
    const k = iso(d);
    if (dayOff(d)) continue;
    const s = SLOTS.find(x => !isBusy(k,x) && !isPast(k,x));
    if (s) return RU_DOW[d.getDay()] + ', ' + human(d) + ' — ' + s;
  }
  return 'ближайшие две недели заняты';
}

let chosen = null;
function pick(date, slot, quiet){
  chosen = { date, slot };
  const d = new Date(date + 'T00:00:00');
  $('#pickLine').textContent = RU_DOW[d.getDay()] + ', ' + human(d) + ', ' + slot;
  document.querySelectorAll('#slotGrid .slot').forEach(b => b.classList.toggle('sel', b.dataset.s === slot));
  if (quiet) return;
  $('#bkName').focus({ preventScroll:true });
  $('#bkForm').scrollIntoView({ behavior:'smooth', block:'nearest' });
}

function bookingText(){
  const d = new Date(chosen.date + 'T00:00:00');
  const svc = $('#svcSel').value;
  return 'Здравствуйте! Хочу записаться: ' + svc + '. '
    + RU_DOW[d.getDay()] + ', ' + human(d) + ', ' + chosen.slot + '. '
    + $('#bkName').value.trim() + ', ' + $('#bkPhone').value.trim()
    + ($('#bkNote').value.trim() ? '. ' + $('#bkNote').value.trim() : '');
}

function submitBooking(e){
  e.preventDefault();
  if (!chosen) { toast('Сначала выберите свободное окно'); return; }
  if (!$('#bkName').value.trim() || $('#bkPhone').value.trim().length < 6){
    toast('Заполните имя и телефон — по ним мастер подтвердит запись'); return;
  }
  const txt = bookingText();
  try { navigator.clipboard && navigator.clipboard.writeText(txt); } catch (err) {}
  $('#bkMsg').textContent = txt;
  $('#bkMsg').hidden = false;
  setBusy(chosen.date, chosen.slot, true);
  renderDays(); renderSlots();
  toast('Заявка готова — текст скопирован, открываем ВК');
  window.open(VK_URL, '_blank', 'noopener');
}

let tt;
function toast(m){
  const t = $('#toast'); t.textContent = m; t.classList.add('on');
  clearTimeout(tt); tt = setTimeout(() => t.classList.remove('on'), 3000);
}

function toggleMaster(){
  master = !master;
  document.body.classList.toggle('master', master);
  $('#masterBtn').textContent = master ? 'Выйти из режима мастера' : 'Я мастер';
  $('#calNote').textContent = master
    ? 'Режим мастера: нажимайте на время, чтобы закрыть или открыть окно. Сохраняется в этом браузере.'
    : 'Выберите день и свободное время — заявка уйдёт мастеру в личные сообщения ВК.';
  renderSlots();
}

function boot(){
  $('#svcSel').innerHTML = SERVICES.map(s => '<option>' + s.n + ' — ' + s.p + ' ₽</option>').join('');
  $('#priceList').innerHTML = SERVICES.map(s =>
    '<li><span class="pn">' + s.n + '</span><span class="pd">' + s.d + ' мин</span><span class="pp">' + s.p + ' ₽</span></li>').join('');
  $('#masterBtn').addEventListener('click', toggleMaster);
  $('#bkForm').addEventListener('submit', submitBooking);
  if (master){ master = false; toggleMaster(); }
  renderDays(); renderSlots();
  const k = iso(active);
  const first = SLOTS.find(s => !isBusy(k,s) && !isPast(k,s));
  if (first) pick(k, first, true);
  renderSlots();
}
document.addEventListener('DOMContentLoaded', boot);
