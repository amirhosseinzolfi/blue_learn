// Configure request interceptor to automatically add authorization header if token exists
axios.interceptors.request.use(
    config => {
        const token = localStorage.getItem('token');
        if (token) {
            config.headers['Authorization'] = `Bearer ${token}`;
        }
        return config;
    },
    error => {
        return Promise.reject(error);
    }
);

// All API calls — returns data or throws
const api = {
    get: (path) => axios.get(`${API_BASE}${path}`).then(r => r.data),
    post: (path, body, opts) => axios.post(`${API_BASE}${path}`, body, opts).then(r => r.data),
    patch: (path, body) => axios.patch(`${API_BASE}${path}`, body).then(r => r.data),
    delete: (path) => axios.delete(`${API_BASE}${path}`).then(r => r.data),

    login:    (username, password) => api.post('/login', { username, password }),
    register: (username, password, full_name, age, job_education) => api.post('/register', { username, password, full_name, age, job_education }),
    fetchMe:  () => api.get('/me'),

    fetchCourses:  () => api.get('/courses/'),
    fetchStats:    () => api.get('/stats'),
    fetchInsights: () => api.get('/insights'),
    fetchSettings: () => api.get('/settings'),

    fetchCourse:      (id) => api.get(`/courses/${id}`),
    fetchChatHistory: (id) => api.get(`/courses/${id}/chat-history`),
    generateMicro:    (id, generateCover = false) => api.post(`/courses/${id}/generate-micro?generate_cover=${generateCover}`),
    generateItem:     (id, generateCover = false) => api.post(`/items/${id}/generate?generate_cover=${generateCover}`),
    completeItem:     (id) => api.post(`/items/${id}/complete`),
    syncStudyTime:    (id, seconds) => api.post(`/items/${id}/study-time`, { seconds }),
    deleteCourse:     (id) => api.delete(`/courses/${id}`),
    patchCourse:      (id, body) => api.patch(`/courses/${id}`, body),
    uploadCover:      (id, file) => {
        const fd = new FormData();
        fd.append('file', file);
        return api.post(`/courses/${id}/cover`, fd, { headers: { 'Content-Type': 'multipart/form-data' } });
    },

    // ── Global Courses catalog (publish / browse / enroll / rate) ──
    fetchGlobalCourses:  (search = null, sort = 'recent') => {
        const params = new URLSearchParams();
        if (search && search.trim()) params.set('search', search.trim());
        if (sort) params.set('sort', sort);
        const q = params.toString();
        return api.get(`/global-courses/${q ? '?' + q : ''}`);
    },
    fetchGlobalCourse:   (id)    => api.get(`/global-courses/${id}`),  // includes items (outline)
    fetchEnrolledIds:    ()      => api.get('/global-courses/enrolled-ids'),
    publishCourse:       (id)    => api.post(`/courses/${id}/publish`),
    unpublishCourse:     (id)    => api.post(`/courses/${id}/unpublish`),
    enrollGlobalCourse:  (id)    => api.post(`/global-courses/${id}/enroll`),
    rateGlobalCourse:    (id, rating) => api.post(`/global-courses/${id}/rate`, { rating }),

    fetchDailyMicro: (count, courseIds, excludeIds) => {
        let url = `/daily-micro-courses?count=${count}`;
        if (courseIds && courseIds.length) url += `&course_ids=${courseIds.join(',')}`;
        if (excludeIds && excludeIds.length) url += `&exclude_ids=${excludeIds.join(',')}`;
        return api.get(url);
    },

    saveSettings:    (data) => api.post('/settings', data),
    generateInsight: ()     => api.post('/generate-insight'),
    rebuildProfile:  ()     => api.post('/profile/rebuild'),

    chatCourseGen: (messages, level = null, duration_sessions = null, learning_style = null, conversation_summary = null, profile = null) => 
        api.post('/chat/course-generator', { messages, level, duration_sessions, learning_style, conversation_summary, profile }),

    coachStream: async (courseId, itemId, message, onChunk) => {
        const headers = { 'Content-Type': 'application/json' };
        const token = localStorage.getItem('token');
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }
        const res = await fetch(`${API_BASE}/chat/coach`, {
            method: 'POST',
            headers: headers,
            body: JSON.stringify({ message, course_id: courseId, item_id: itemId })
        });
        if (!res.ok) throw new Error('Network error');
        const reader = res.body.getReader();
        const dec = new TextDecoder('utf-8');
        let done = false;
        let full = '';
        while (!done) {
            const { value, done: d } = await reader.read();
            done = d;
            if (value) { full += dec.decode(value, { stream: true }); onChunk(full); }
        }
    }
};
