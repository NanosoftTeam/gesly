let currentContact = { name: 'Conversation', avatar: '💬' };

const knownUsersStorageKey = 'geslyKnownUsers';
const dbRefreshIntervalMs = 3000;
let knownUsers = {};
let latestOnlineUsers = [];
let latestDbSignature = '';
let refreshInProgress = false;
let myUsername = localStorage.getItem('geslyUsername') || 'xX_DarkAngel_Xx';

function loadKnownUsersFromLocalStorage() {
  try {
    return JSON.parse(localStorage.getItem(knownUsersStorageKey)) || {};
  } catch {
    return {};
  }
}

async function loadKnownUsers() {
  if (!window.require) {
    knownUsers = loadKnownUsersFromLocalStorage();
    return knownUsers;
  }

  const { ipcRenderer } = require('electron');
  try {
    const envUsers = await ipcRenderer.invoke('load-offline-users');
    const legacyUsers = loadKnownUsersFromLocalStorage();
    knownUsers = { ...legacyUsers, ...envUsers };
    await saveOfflineUsers(knownUsers);
  } catch (error) {
    console.error('Failed to load offline users from .env:', error);
    knownUsers = loadKnownUsersFromLocalStorage();
  }

  return knownUsers;
}

function getOfflineUsersMap(onlineUsers) {
  const onlineByName = new Map(onlineUsers.map((user) => [user.name, user]));
  return Object.fromEntries(
    Object.entries(knownUsers)
      .filter(([name]) => !onlineByName.has(name))
      .sort(([a], [b]) => a.localeCompare(b))
  );
}

async function saveOfflineUsers(offlineUsers) {
  if (!window.require) {
    localStorage.setItem(knownUsersStorageKey, JSON.stringify(offlineUsers));
    return;
  }

  const { ipcRenderer } = require('electron');
  try {
    await ipcRenderer.invoke('save-offline-users', offlineUsers);
  } catch (error) {
    console.error('Failed to save offline users to .env:', error);
  }
}

function getUsersSignature(users) {
  return users
    .map((user) => `${user.name}|${user.endpoint}`)
    .sort()
    .join('\n');
}

function avatarForName(name) {
  const avatars = ['🌸', '🤘', '💜', '🎧', '😎', '💬', '✨', '🟢'];
  const index = [...name].reduce((sum, char) => sum + char.charCodeAt(0), 0) % avatars.length;
  return avatars[index];
}

function openChat(user, avatar) {
  currentContact = { ...user, avatar };

  if (window.require) {
    const { ipcRenderer } = require('electron');
    ipcRenderer.send('open-chat-window', currentContact);
    return;
  }

  const params = new URLSearchParams(currentContact);
  window.open(`chat.html?${params.toString()}`, '_blank');
}

async function promptForUsername() {
  const username = window.prompt('Enter your username:', myUsername)?.trim();
  if (!username) {
    return;
  }

  myUsername = username;
  localStorage.setItem('geslyUsername', myUsername);

  const usernameBox = document.getElementById('myUsername');
  if (usernameBox) {
    usernameBox.textContent = myUsername;
  }

  if (!window.require) {
    return;
  }

  const { ipcRenderer } = require('electron');
  try {
    const currentUser = await ipcRenderer.invoke('register-current-user', myUsername);
    knownUsers[currentUser.name] = {
      ...knownUsers[currentUser.name],
      ...currentUser,
      lastSeenAt: new Date().toISOString()
    };
    const onlineUsersWithCurrent = latestOnlineUsers.filter((user) => user.name !== currentUser.name);
    onlineUsersWithCurrent.push(currentUser);
    await saveOfflineUsers(getOfflineUsersMap(onlineUsersWithCurrent));
    latestDbSignature = '';
    await refreshRentryUsers();
  } catch (error) {
    window.alert(`Could not put you online in DB: ${error.message}`);
  }
}

function createContactItem(user, isOnline) {
  const item = document.createElement('div');
  const avatar = avatarForName(user.name);
  item.className = `contact-item gradient-contact-hover flex items-center gap-2 px-4 py-1 border-b border-[#eef5fc] ${isOnline ? 'cursor-pointer' : 'opacity-55'}`;

  if (isOnline) {
    item.addEventListener('click', () => openChat(user, avatar));
  }

  const dotColor = isOnline ? 'bg-green-500' : 'bg-gray-400';
  const statusText = isOnline ? user.endpoint : `Offline - last seen at ${user.endpoint || 'unknown address'}`;

  const avatarBox = document.createElement('div');
  avatarBox.className = `relative w-8 h-8 flex-shrink-0 flex items-center justify-center rounded-sm border border-[#7aaacf] text-sm ${isOnline ? '' : 'bg-gray-100'}`;
  if (isOnline) {
    avatarBox.style.background = 'linear-gradient(135deg,#e8f0fd,#b8c8f8)';
  }
  avatarBox.textContent = avatar;

  const statusDot = document.createElement('div');
  statusDot.className = `status-dot absolute -bottom-0.5 -right-0.5 w-2 h-2 rounded-full border border-white ${dotColor}`;
  avatarBox.appendChild(statusDot);

  const textBox = document.createElement('div');
  textBox.className = 'flex-1 min-w-0';

  const name = document.createElement('div');
  name.className = `text-[12px] ${isOnline ? 'font-bold' : ''} text-[#1a3e6b] truncate`;
  name.textContent = user.name;

  const subtitle = document.createElement('div');
  subtitle.className = 'text-[10px] text-[#6688aa] italic truncate';
  subtitle.textContent = statusText;

  textBox.append(name, subtitle);
  item.append(avatarBox, textBox);

  return item;
}

function createEmptyContactItem(text) {
  const item = document.createElement('div');
  item.className = 'px-4 py-2 border-b border-[#eef5fc] text-[11px] text-[#6688aa] italic';
  item.textContent = text;
  return item;
}

function setGroupCount(group, count) {
  const label = document.getElementById(`${group}-count`);
  if (label) {
    label.textContent = `${group === 'online' ? 'Online' : 'Offline'} (${count})`;
  }
}

function renderContacts(onlineUsers) {
  const onlineByName = new Map(onlineUsers.map((user) => [user.name, user]));

  onlineUsers.forEach((user) => {
    knownUsers[user.name] = {
      ...knownUsers[user.name],
      ...user,
      lastSeenAt: new Date().toISOString()
    };
  });

  const offlineUsers = Object.values(knownUsers)
    .filter((user) => !onlineByName.has(user.name))
    .sort((a, b) => a.name.localeCompare(b.name));
  saveOfflineUsers(getOfflineUsersMap(onlineUsers));

  const contactsOnline = document.getElementById('contacts-online');
  const contactsOffline = document.getElementById('contacts-offline');
  contactsOnline.replaceChildren();
  contactsOffline.replaceChildren();

  if (onlineUsers.length) {
    onlineUsers
      .slice()
      .sort((a, b) => a.name.localeCompare(b.name))
      .forEach((user) => contactsOnline.appendChild(createContactItem(user, true)));
  } else {
    contactsOnline.appendChild(createEmptyContactItem('No users currently online.'));
  }

  if (offlineUsers.length) {
    offlineUsers.forEach((user) => contactsOffline.appendChild(createContactItem(user, false)));
  } else {
    contactsOffline.appendChild(createEmptyContactItem('No offline users loaded yet.'));
  }

  setGroupCount('online', onlineUsers.length);
  setGroupCount('offline', offlineUsers.length);
  filterContacts();
}

async function refreshRentryUsers() {
  if (refreshInProgress) {
    return;
  }

  if (!window.require) {
    renderContacts(latestOnlineUsers);
    return;
  }

  const { ipcRenderer } = require('electron');
  refreshInProgress = true;

  try {
    const onlineUsers = await ipcRenderer.invoke('get-rentry-users');
    const dbSignature = getUsersSignature(onlineUsers);

    if (dbSignature === latestDbSignature) {
      return;
    }

    latestDbSignature = dbSignature;
    latestOnlineUsers = onlineUsers;
    renderContacts(latestOnlineUsers);
  } catch (error) {
    console.error('Failed to load Rentry users:', error);
    if (!latestDbSignature) {
      renderContacts(latestOnlineUsers);
    }
  } finally {
    refreshInProgress = false;
  }
}

function toggleGroup(group) {
  const contacts = document.getElementById('contacts-' + group);
  const arrow = document.getElementById('arrow-' + group);
  const hidden = contacts.style.display === 'none';
  contacts.style.display = hidden ? '' : 'none';
  arrow.style.transform = hidden ? '' : 'rotate(-90deg)';
}

function filterContacts() {
  const q = document.getElementById('searchBox').value.toLowerCase();
  document.querySelectorAll('.contact-item').forEach((item) => {
    const name = item.querySelector('.text-\\[12px\\]')?.textContent.toLowerCase() || '';
    item.style.display = name.includes(q) ? '' : 'none';
  });
}

function updateStatus() {
  const val = document.getElementById('myStatus').value;
  const dot = document.getElementById('myStatusDot');
  dot.className = 'absolute -bottom-0.5 -right-0.5 w-2.5 h-2.5 rounded-full border-2 border-white ';
  const colors = { online: 'bg-green-500', away: 'bg-yellow-400', busy: 'bg-red-500', offline: 'bg-gray-400' };
  dot.className += colors[val] || 'bg-green-500';
}

window.addEventListener('DOMContentLoaded', async () => {
  const usernameBox = document.getElementById('myUsername');
  if (usernameBox) {
    usernameBox.textContent = myUsername;
  }

  await loadKnownUsers();
  renderContacts(latestOnlineUsers);
  promptForUsername().finally(refreshRentryUsers);
  setInterval(refreshRentryUsers, dbRefreshIntervalMs);
  window.addEventListener('focus', refreshRentryUsers);
  document.addEventListener('visibilitychange', () => {
    if (!document.hidden) {
      refreshRentryUsers();
    }
  });
});
