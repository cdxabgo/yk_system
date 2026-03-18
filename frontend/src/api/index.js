import request from './request'

export const authApi = {
  login: (data) => request.post('/auth/login', data),
  logout: () => request.post('/auth/logout')
}

export const employeeApi = {
  list: (params) => request.get('/employee/list', { params }),
  getById: (id) => request.get(`/employee/${id}`),
  add: (data) => request.post('/employee', data),
  update: (id, data) => request.put(`/employee/${id}`, data),
  delete: (id) => request.delete(`/employee/${id}`)
}

export const diseaseApi = {
  list: (params) => request.get('/disease/list', { params }),
  getById: (id) => request.get(`/disease/${id}`),
  add: (data) => request.post('/disease', data),
  update: (id, data) => request.put(`/disease/${id}`, data),
  delete: (id) => request.delete(`/disease/${id}`)
}

export const heartRateApi = {
  list: (params) => request.get('/heartRate/list', { params }),
  getById: (id) => request.get(`/heartRate/${id}`),
  add: (data) => request.post('/heartRate', data),
  delete: (id) => request.delete(`/heartRate/${id}`),
  monitor: (params) => request.get('/heartRate/monitor', { params }),
  latest: () => request.get('/heartRate/latest')
}

export const healthAdviceApi = {
  generate: (employeeId) => request.get('/healthAdvice/generate', { params: { employeeId } })
}
