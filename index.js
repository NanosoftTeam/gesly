const dgram = require('node:dgram')
const fs = require('node:fs/promises')
const path = require('node:path')
const { app, BrowserWindow, ipcMain } = require('electron/main')

const RENTRY_BASE_URL = 'https://rentry.co'
const RENTRY_TUNNEL_NAME = 'tunnel-system-gesly'
const RENTRY_EDIT_CODE = 'GeslySystemPassword123'
const LOCAL_CHAT_PORT = 6676
const ENV_PATH = path.join(__dirname, '.env')
const OFFLINE_USERS_ENV_KEY = 'gesly-offline-users'

const chatWindowsByEndpoint = new Map()
let cachedUsers = []
let currentUsername = ''
let udpSocket = null
let udpReady = null
let appIsQuitting = false

const parseEnvFile = (content) => {
  const values = {}

  content
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter((line) => line && !line.startsWith('#'))
    .forEach((line) => {
      const separatorIndex = line.indexOf('=')
      if (separatorIndex === -1) {
        return
      }

      const key = line.slice(0, separatorIndex).trim()
      const value = line.slice(separatorIndex + 1).trim()
      if (key) {
        values[key] = value
      }
    })

  return values
}

const readEnvContent = async () => {
  try {
    return await fs.readFile(ENV_PATH, 'utf8')
  } catch (error) {
    if (error.code === 'ENOENT') {
      return ''
    }
    throw error
  }
}

const readEnvValues = async () => {
  return parseEnvFile(await readEnvContent())
}

const writeEnvValue = async (key, value) => {
  const content = await readEnvContent()
  const lines = content ? content.split(/\r?\n/) : []
  let found = false
  const nextLines = lines.map((line) => {
    const separatorIndex = line.indexOf('=')
    const lineKey = separatorIndex === -1 ? '' : line.slice(0, separatorIndex).trim()

    if (lineKey !== key) {
      return line
    }

    found = true
    return `${key}=${value}`
  })

  if (!found) {
    if (nextLines.length && nextLines[nextLines.length - 1] !== '') {
      nextLines.push('')
    }
    nextLines.push(`${key}=${value}`)
  }

  await fs.writeFile(ENV_PATH, nextLines.join('\n').replace(/\n*$/, '\n'), 'utf8')
}

const loadEnvIntoProcess = async () => {
  const values = await readEnvValues()
  Object.entries(values).forEach(([key, value]) => {
    if (!process.env[key]) {
      process.env[key] = value
    }
  })
}

const loadOfflineUsers = async () => {
  const values = await readEnvValues()
  const encodedUsers = values[OFFLINE_USERS_ENV_KEY]
  if (!encodedUsers) {
    return {}
  }

  try {
    const json = Buffer.from(encodedUsers, 'base64').toString('utf8')
    const users = JSON.parse(json)
    return users && typeof users === 'object' && !Array.isArray(users) ? users : {}
  } catch {
    return {}
  }
}

const saveOfflineUsers = async (users) => {
  const safeUsers = users && typeof users === 'object' && !Array.isArray(users) ? users : {}
  const encodedUsers = Buffer.from(JSON.stringify(safeUsers), 'utf8').toString('base64')
  await writeEnvValue(OFFLINE_USERS_ENV_KEY, encodedUsers)
  return safeUsers
}

const getRentryHeaders = () => {
  const headers = {
    Referer: RENTRY_BASE_URL
  }
  const auth = process.env['rentry-auth']
  if (auth) {
    headers['rentry-auth'] = auth
  }
  return headers
}

const getCsrfToken = async () => {
  const response = await fetch(RENTRY_BASE_URL, {
    headers: getRentryHeaders()
  })
  const cookies = response.headers.getSetCookie?.() || [response.headers.get('set-cookie')].filter(Boolean)
  const csrfCookie = cookies.find((cookie) => cookie.includes('csrftoken='))
  const token = csrfCookie?.match(/csrftoken=([^;]+)/)?.[1]

  if (!token) {
    throw new Error('Could not read Rentry CSRF token')
  }

  return {
    token,
    cookie: `csrftoken=${token}`
  }
}

const parseRentryUsers = (content) => {
  return content
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => line.match(/^(?:-\s*)?(.+?)\s*-\s+(.+)$/))
    .filter(Boolean)
    .map((match) => {
      const endpoint = match[2].trim()
      const [ip, port] = endpoint.split(':')

      return {
        name: match[1].trim(),
        endpoint,
        ip: ip || '',
        port: port || ''
      }
    })
}

const fetchRentryUsers = async () => {
  const csrf = await getCsrfToken()
  const body = new URLSearchParams({
    csrfmiddlewaretoken: csrf.token,
    text: RENTRY_TUNNEL_NAME
  })

  const response = await fetch(`${RENTRY_BASE_URL}/api/raw/${RENTRY_TUNNEL_NAME}`, {
    method: 'POST',
    headers: {
      ...getRentryHeaders(),
      Cookie: csrf.cookie,
      'Content-Type': 'application/x-www-form-urlencoded'
    },
    body
  })

  const text = await response.text()

  if (text.includes('errors')) {
    throw new Error(`Rentry raw request failed: ${text}`)
  }

  const data = JSON.parse(text)
  cachedUsers = parseRentryUsers(data.content || '')
  return cachedUsers
}

const getPublicIp = async () => {
  const response = await fetch('https://api.ipify.org')
  const ip = (await response.text()).trim()

  if (!ip) {
    throw new Error('Could not read public IP address')
  }

  return ip
}

const writeRentryUsers = async (users) => {
  const csrf = await getCsrfToken()
  const text = users.map((user) => `${user.name}- ${user.endpoint}`).join('\n')
  const body = new URLSearchParams({
    csrfmiddlewaretoken: csrf.token,
    text,
    edit_code: RENTRY_EDIT_CODE
  })

  const response = await fetch(`${RENTRY_BASE_URL}/api/edit/${RENTRY_TUNNEL_NAME}`, {
    method: 'POST',
    headers: {
      ...getRentryHeaders(),
      Cookie: csrf.cookie,
      'Content-Type': 'application/x-www-form-urlencoded'
    },
    body
  })

  const result = await response.text()
  if (result.includes('errors')) {
    throw new Error(`Rentry edit request failed: ${result}`)
  }

  cachedUsers = users
  return users
}

const registerCurrentUser = async (username) => {
  const cleanUsername = username.trim()
  if (!cleanUsername) {
    throw new Error('Username cannot be empty')
  }

  const publicIp = await getPublicIp()
  const endpoint = `${publicIp}:${LOCAL_CHAT_PORT}`
  const users = await fetchRentryUsers()
  const nextUsers = users.filter((user) => user.name !== cleanUsername)
  const currentUser = {
    name: cleanUsername,
    endpoint,
    ip: publicIp,
    port: String(LOCAL_CHAT_PORT)
  }

  nextUsers.push(currentUser)
  await writeRentryUsers(nextUsers)
  currentUsername = cleanUsername
  return currentUser
}

const unregisterCurrentUser = async () => {
  if (!currentUsername) {
    return
  }

  try {
    const users = await fetchRentryUsers()
    await writeRentryUsers(users.filter((user) => user.name !== currentUsername))
  } finally {
    currentUsername = ''
  }
}

const getContactForEndpoint = (endpoint) => {
  return cachedUsers.find((user) => user.endpoint === endpoint) || {
    name: endpoint,
    endpoint,
    ip: endpoint.split(':')[0] || '',
    port: endpoint.split(':')[1] || ''
  }
}

const registerChatWindow = (chatWin, contact) => {
  const endpoint = contact?.endpoint
  if (!endpoint) {
    return
  }

  if (!chatWindowsByEndpoint.has(endpoint)) {
    chatWindowsByEndpoint.set(endpoint, new Set())
  }

  chatWindowsByEndpoint.get(endpoint).add(chatWin)
  chatWin.on('closed', () => {
    const windows = chatWindowsByEndpoint.get(endpoint)
    if (!windows) {
      return
    }

    windows.delete(chatWin)
    if (windows.size === 0) {
      chatWindowsByEndpoint.delete(endpoint)
    }
  })
}

const sendToChatWindows = (endpoint, payload) => {
  const windows = chatWindowsByEndpoint.get(endpoint)
  if (!windows) {
    return false
  }

  windows.forEach((chatWin) => {
    if (!chatWin.isDestroyed()) {
      chatWin.webContents.send('incoming-chat-message', payload)
    }
  })
  return true
}

const createWindow = () => {
  let win = new BrowserWindow({
    width: 315,
    height: 700,
    frame: false,
    resizable: false,
    maximizable: false,
    fullscreenable: false,
    useContentSize: true,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false
    }
  })

  win.on('closed', () => {
    app.quit()
  })

  win.loadFile('index.html')
}

const createChatWindow = (contact) => {
  const name = contact?.name || 'Conversation'
  const avatar = contact?.avatar || 'Chat'
  const endpoint = contact?.endpoint || ''
  const ip = contact?.ip || ''
  const port = contact?.port || ''

  let chatWin = new BrowserWindow({
    width: 400,
    height: 440,
    frame: false,
    resizable: false,
    maximizable: false,
    fullscreenable: false,
    useContentSize: true,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false
    }
  })

  registerChatWindow(chatWin, { ...contact, endpoint })

  chatWin.loadFile('chat.html', {
    query: { name, avatar, endpoint, ip, port }
  })

  return chatWin
}

const openIncomingChatWindow = (contact, message) => {
  const chatWin = createChatWindow(contact)
  chatWin.webContents.once('did-finish-load', () => {
    chatWin.webContents.send('incoming-chat-message', message)
  })
}

const handleIncomingUdpMessage = (buffer, remote) => {
  const text = buffer.toString('utf8')
  const endpoint = `${remote.address}:${remote.port}`
  const contact = getContactForEndpoint(endpoint)
  const payload = {
    text,
    from: contact.name,
    endpoint
  }

  if (!sendToChatWindows(endpoint, payload)) {
    openIncomingChatWindow(contact, payload)
  }
}

const startUdpSocket = () => {
  if (udpReady) {
    return udpReady
  }

  udpReady = new Promise((resolve, reject) => {
    udpSocket = dgram.createSocket({ type: 'udp4', reuseAddr: true })

    udpSocket.on('message', handleIncomingUdpMessage)
    udpSocket.on('error', (error) => {
      console.error('UDP chat socket error:', error)
      reject(error)
    })
    udpSocket.once('listening', resolve)
    udpSocket.bind(LOCAL_CHAT_PORT, '0.0.0.0')
  })

  return udpReady
}

const sendUdpMessage = async (contact, text) => {
  await startUdpSocket()

  const ip = contact?.ip
  const port = Number(contact?.port)

  if (!ip || !Number.isInteger(port) || port <= 0 || port > 65535) {
    throw new Error(`Invalid peer endpoint: ${contact?.endpoint || ''}`)
  }

  return new Promise((resolve, reject) => {
    udpSocket.send(Buffer.from(text, 'utf8'), port, ip, (error) => {
      if (error) {
        reject(error)
        return
      }
      resolve()
    })
  })
}

app.whenReady().then(async () => {
  await loadEnvIntoProcess()

  startUdpSocket().catch((error) => {
    console.error('Could not start UDP chat socket:', error)
  })

  ipcMain.handle('get-rentry-users', async () => {
    return fetchRentryUsers()
  })

  ipcMain.handle('register-current-user', async (_event, username) => {
    return registerCurrentUser(username)
  })

  ipcMain.handle('load-offline-users', async () => {
    return loadOfflineUsers()
  })

  ipcMain.handle('save-offline-users', async (_event, users) => {
    return saveOfflineUsers(users)
  })

  ipcMain.handle('send-chat-message', async (_event, payload) => {
    await sendUdpMessage(payload.contact, payload.text)
    return { ok: true }
  })

  ipcMain.on('open-chat-window', (_event, contact) => {
    createChatWindow(contact)
  })

  createWindow()

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow()
    }
  })
})

app.on('window-all-closed', () => {
  if (udpSocket) {
    udpSocket.close()
  }

  if (process.platform !== 'darwin') {
    app.quit()
  }
})

app.on('before-quit', (event) => {
  if (appIsQuitting || !currentUsername) {
    return
  }

  event.preventDefault()
  appIsQuitting = true
  unregisterCurrentUser()
    .catch((error) => {
      console.error('Could not remove current user from DB:', error)
    })
    .finally(() => {
      app.quit()
    })
})
