import { http, HttpResponse } from 'msw'

let mockSession: { token?: string; user?: any } = {}

export const handlers = [
  http.post('/api/auth/login', async ({ request }) => {
    const body = await request.json() as any
    if (body.username === 'alice' && body.password === 'secret') {
      mockSession = { token: 'mock-jwt-token', user: { id:'u1', name:'Alice', role:'user' } }
      return HttpResponse.json({ accessToken: mockSession.token, user: mockSession.user })
    }
    return HttpResponse.json({ message: 'invalid credentials' }, { status: 401 })
  }),
  http.get('/api/auth/me', async () => {
    if (mockSession.user) return HttpResponse.json({ user: mockSession.user })
    return HttpResponse.json({ message: 'unauthorized' }, { status: 401 })
  }),
  http.post('/api/auth/logout', async () => {
    mockSession = {}; return HttpResponse.json({ ok: true })
  }),

  http.post('/api/ess/validate', async ({ request }) => {
    const body = await request.json() as any
    const success = body?.content && body?.checksum && Array.isArray(body?.rules)
    return HttpResponse.json({
      report: { reports: { [body.rules?.[0] || 'AUNZ_PEPPOL_SB_1_0_10']: { successful: true, firedAssertionErrors: [] } } }
    }, { status: success ? 200 : 400 })
  }),

  http.post('/api/schema/validate', async ({ request }) => {
    const xml = await request.text()
    const ok = xml.includes('<Invoice')
    return HttpResponse.json({ ok, messages: ok ? [] : ['Not an Invoice root element'] }, { status: ok ? 200 : 400 })
  }),

  http.post('/api/send', async ({ request }) => {
    const body = (await request.json()) as any
    if (!body?.xml) return HttpResponse.json({ ok:false, message:'Missing xml' }, { status: 400 })
    return HttpResponse.json({ ok:true, channel: body.channel||'email', deliveryId:'DLV-'+Math.random().toString(36).slice(2,8), status:'queued', time:new Date().toISOString() })
  }),
]
