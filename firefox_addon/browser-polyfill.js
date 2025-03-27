/**
 * Browser API Compatibility Layer for Chrome and Firefox
 * This script provides a unified API that works across both browsers
 */

;(() => {
    // Check if we're in a browser extension context
    if (typeof browser === "undefined" && typeof chrome !== "undefined") {
      // We're in Chrome, create a browser object that mimics Firefox's API
      window.browser = {
        // Storage API
        storage: {
          local: {
            get: (keys) =>
              new Promise((resolve, reject) => {
                try {
                  chrome.storage.local.get(keys, (result) => {
                    if (chrome.runtime.lastError) {
                      reject(chrome.runtime.lastError)
                    } else {
                      resolve(result)
                    }
                  })
                } catch (error) {
                  reject(error)
                }
              }),
            set: (items) =>
              new Promise((resolve, reject) => {
                try {
                  chrome.storage.local.set(items, () => {
                    if (chrome.runtime.lastError) {
                      reject(chrome.runtime.lastError)
                    } else {
                      resolve()
                    }
                  })
                } catch (error) {
                  reject(error)
                }
              }),
            remove: (keys) =>
              new Promise((resolve, reject) => {
                try {
                  chrome.storage.local.remove(keys, () => {
                    if (chrome.runtime.lastError) {
                      reject(chrome.runtime.lastError)
                    } else {
                      resolve()
                    }
                  })
                } catch (error) {
                  reject(error)
                }
              }),
          },
        },
  
        // Tabs API
        tabs: {
          query: (queryInfo) =>
            new Promise((resolve, reject) => {
              try {
                chrome.tabs.query(queryInfo, (tabs) => {
                  if (chrome.runtime.lastError) {
                    reject(chrome.runtime.lastError)
                  } else {
                    resolve(tabs)
                  }
                })
              } catch (error) {
                reject(error)
              }
            }),
        },
  
        // Scripting API
        scripting: {
          executeScript: (details) =>
            new Promise((resolve, reject) => {
              try {
                // Handle both Chrome's callback-based API and Firefox's Promise-based API
                if (chrome.scripting) {
                  // Chrome MV3 scripting API
                  chrome.scripting.executeScript(details, (results) => {
                    if (chrome.runtime.lastError) {
                      reject(chrome.runtime.lastError)
                    } else {
                      resolve(results)
                    }
                  })
                } else if (chrome.tabs && chrome.tabs.executeScript) {
                  // Chrome MV2 tabs.executeScript API
                  const { target, func, args } = details
                  const tabId = target?.tabId
  
                  // Convert function to string
                  let code = func.toString()
  
                  // If args are provided, wrap the function call with arguments
                  if (args && args.length > 0) {
                    // Create a self-executing function with the args
                    code = `(${code})(${args.map((arg) => JSON.stringify(arg)).join(",")})`
                  } else {
                    // Just execute the function
                    code = `(${code})()`
                  }
  
                  chrome.tabs.executeScript(tabId, { code }, (results) => {
                    if (chrome.runtime.lastError) {
                      reject(chrome.runtime.lastError)
                    } else {
                      // Format results to match Chrome's scripting API
                      const formattedResults = results.map((result) => ({ result }))
                      resolve(formattedResults)
                    }
                  })
                } else {
                  reject(new Error("No scripting API available"))
                }
              } catch (error) {
                reject(error)
              }
            }),
        },
  
        // Runtime API
        runtime: {
          getURL: (path) => chrome.runtime.getURL(path),
          lastError: chrome.runtime.lastError,
        },
      }
    } else if (typeof browser !== "undefined") {
      // We're in Firefox, browser object already exists
      // But we might need to add some Chrome-compatible methods
  
      // Ensure chrome object exists for compatibility
      if (typeof chrome === "undefined") {
        window.chrome = {
          storage: browser.storage,
          tabs: browser.tabs,
          scripting: browser.scripting,
          runtime: browser.runtime,
        }
      }
    } else {
      // We're not in a browser extension context, create mock objects for development
      console.warn("Not in a browser extension context. Creating mock browser API objects.")
  
      // Create a simple localStorage-based mock for storage
      const mockStorage = {}
  
      window.browser = {
        storage: {
          local: {
            get: (keys) =>
              new Promise((resolve) => {
                if (keys === null) {
                  resolve(JSON.parse(JSON.stringify(mockStorage)))
                  return
                }
  
                const result = {}
                if (Array.isArray(keys)) {
                  keys.forEach((key) => {
                    if (key in mockStorage) {
                      result[key] = JSON.parse(JSON.stringify(mockStorage[key]))
                    }
                  })
                } else if (typeof keys === "string") {
                  if (keys in mockStorage) {
                    result[keys] = JSON.parse(JSON.stringify(mockStorage[keys]))
                  }
                } else if (typeof keys === "object") {
                  Object.keys(keys).forEach((key) => {
                    result[key] = key in mockStorage ? JSON.parse(JSON.stringify(mockStorage[key])) : keys[key]
                  })
                }
                resolve(result)
              }),
            set: (items) =>
              new Promise((resolve) => {
                Object.keys(items).forEach((key) => {
                  mockStorage[key] = JSON.parse(JSON.stringify(items[key]))
                })
                resolve()
              }),
            remove: (keys) =>
              new Promise((resolve) => {
                if (typeof keys === "string") {
                  delete mockStorage[keys]
                } else if (Array.isArray(keys)) {
                  keys.forEach((key) => delete mockStorage[key])
                }
                resolve()
              }),
          },
        },
  
        tabs: {
          query: () => Promise.resolve([{ id: 1, url: window.location.href }]),
        },
  
        scripting: {
          executeScript: () => Promise.resolve([{ result: null }]),
        },
  
        runtime: {
          getURL: (path) => path,
        },
      }
  
      window.chrome = window.browser
    }
  })()
  
  