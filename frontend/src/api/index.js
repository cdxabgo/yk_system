import request from './request'

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
  delete: (id) => request.delete(`/heartRate/${id}`)
}

export const dutyApi = {
  query: (params) => request.get('/duty/query', { params })
}
