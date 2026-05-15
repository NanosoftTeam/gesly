const { ipcRenderer } = require('electron');

const NUDGE_MESSAGE = 'NUDGE';
const PING_MESSAGE = 'PING';
const myUsername = localStorage.getItem('geslyUsername') || 'xX_DarkAngel_Xx';
let currentContact = {
  name: 'Conversation',
  avatar: 'Chat',
  endpoint: '',
  ip: '',
  port: ''
};

function getTime() {
  return new Date().toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit', hour12: true });
}

function setupChatWindow() {
  const params = new URLSearchParams(window.location.search);
  currentContact = {
    name: params.get('name') || 'Conversation',
    avatar: params.get('avatar') || 'Chat',
    endpoint: params.get('endpoint') || '',
    ip: params.get('ip') || '',
    port: params.get('port') || ''
  };

  document.getElementById('chatTitle').textContent = 'Chat with ' + currentContact.name;
  document.getElementById('chatName').textContent = currentContact.name;
  document.getElementById('chatAvatar').textContent = currentContact.avatar;

  ['initSender', 'initSender2'].forEach((id) => {
    const el = document.getElementById(id);
    if (el) el.textContent = currentContact.name;
  });

  ipcRenderer.on('incoming-chat-message', (_event, message) => {
    const text = message.text.trim();

    if (text === PING_MESSAGE) {
      return;
    }

    if (text === NUDGE_MESSAGE) {
      appendNudge(`${message.from || currentContact.name} sent a Nudge!`);
      return;
    }

    appendMessage(message.from || currentContact.name, message.text, 'theirs');
  });

  setTimeout(() => document.getElementById('chatInput').focus(), 100);
  sendWireMessage(PING_MESSAGE).catch((error) => {
    console.error('Initial UDP ping failed:', error);
  });
}

async function sendWireMessage(text) {
  await ipcRenderer.invoke('send-chat-message', {
    contact: currentContact,
    text
  });
}

async function sendMessage() {
  const input = document.getElementById('chatInput');
  const text = input.value.trim();
  if (!text) return;

  appendMessage(myUsername, text, 'mine');
  input.value = '';

  try {
    await sendWireMessage(text);
  } catch (error) {
    appendSystemMessage(`Message failed: ${error.message}`);
  }
}

function appendMessage(sender, text, type) {
  const messages = document.getElementById('chatMessages');
  const isTheirs = type === 'theirs';
  const row = document.createElement('div');
  row.className = 'flex flex-col';

  const senderEl = document.createElement('div');
  senderEl.className = `text-[10px] font-bold mb-0.5 ${isTheirs ? 'text-[#b03030]' : 'text-[#2e6fb0]'}`;
  senderEl.textContent = sender;

  const bodyEl = document.createElement('div');
  bodyEl.className = `max-w-[85%] px-2 py-1 rounded-sm text-[12px] leading-snug ${isTheirs ? 'bg-[#fff0f0] border border-[#e0a0a0]' : 'bg-[#e8f4fe] border border-[#a0c8e8]'}`;
  bodyEl.textContent = text;

  const timeEl = document.createElement('div');
  timeEl.className = 'text-[10px] text-gray-400 mt-0.5';
  timeEl.textContent = getTime();

  row.append(senderEl, bodyEl, timeEl);
  messages.appendChild(row);
  messages.scrollTop = messages.scrollHeight;
}

function appendNudge(text) {
  const messages = document.getElementById('chatMessages');
  const nudge = document.createElement('div');
  nudge.className = 'text-center text-[11px] text-[#e08000] italic py-1';
  nudge.textContent = `\uD83D\uDCA5 ${text}`;
  messages.appendChild(nudge);
  messages.scrollTop = messages.scrollHeight;
}

function appendSystemMessage(text) {
  const messages = document.getElementById('chatMessages');
  const row = document.createElement('div');
  row.className = 'text-center text-[10px] text-[#b03030] italic py-1';
  row.textContent = text;
  messages.appendChild(row);
  messages.scrollTop = messages.scrollHeight;
}

async function sendNudge() {
  appendNudge('You sent a Nudge!');

  try {
    await sendWireMessage(NUDGE_MESSAGE);
  } catch (error) {
    appendSystemMessage(`Nudge failed: ${error.message}`);
  }
}

function handleKey(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
}

window.addEventListener('DOMContentLoaded', setupChatWindow);
