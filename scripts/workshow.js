/**
 * Добавляем во все ссылки, содержащие t.me/workshow_bot параметр ?start= с ClientId/yclid
 * Ссылки вида tg://resolve?domain=<bot_username> не поддерживаются
 * При отсутствии clientId (счётчик метрики заблокирован/не загружен/отсутствует _ym_uid) будет передаваться ymclid__null__
 * При отсутствии yclid в урле будет передаваться yclid__null__
 */
(() => {
  const debug = document.location.search.includes('_tg_debug') ? (...data) => console.log(...data) : () => {}
  const processLinks = (startParam) => {
    const links = document.querySelectorAll('a')
    debug('processLinks', links.length)
    let counter = 0
    links.forEach((link) => {
      const href = link.getAttribute('href')
      if (href?.includes('t.me/workshow_bot')) {
        counter++
        const url = new URL(href)
        url.searchParams.set('start', startParam)
        link.setAttribute('href', url)
      }
    })
    debug('processed', counter)
  }
  const waitForYm = (tries, yclid) => {
    if ('ym' in window) {
      ym(98979849, 'getClientID', (clientId) => {
        debug('getClientID')
        processLinks(`ymclid__${clientId}__yclid__${yclid}__`)
      })
    } else if (tries > 0) {
      debug('retry waitForYm', tries)
      setTimeout(() => waitForYm(tries - 1, yclid), 1000)
    }
  }
  const onLoaded = () => {
    debug('onLoaded', 'ym' in window)
    const clientId = (document.cookie.match(/(?:^|; )_ym_uid=([^;]*)/) ?? [null, null])[1]
    const yclid = (new URL(document.location.href)).searchParams.get('yclid')
    processLinks(`ymclid__${clientId}__yclid__${yclid}__`)
    waitForYm(5, yclid)
  }
  if (document.readyState === 'loading') {
    debug('document is loading')
    document.addEventListener('DOMContentLoaded', onLoaded)
  } else {
    onLoaded()
  }
})()
