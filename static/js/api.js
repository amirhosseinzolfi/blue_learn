// All API calls — returns data or throws
const api = {
    get: (path) => axios.get(`${API_BASE}${path}`).then(r => r.data),
    post: (path, body, opts) => axios.post(`${API_BASE}${path}`, body, opts).then(r => r.data),
    patch: (path, body) => axios.patch(`${API_BASE}${path}`, body).then(r => r.data),
    delete: (path) => axios.delete(`${API_BASE}${path}`).then(r => r.data),

    fetchCourses:  () => api.get('/courses/'),
    fetchStats:    () => api.get('/stats'),
    fetchInsights: () => api.get('/insights'),
    fetchSettings: () => api.get('/settings'),

    fetchCourse:      (id) => api.get(`/courses/${id}`),
    fetchChatHistory: (id) => api.get(`/courses/${id}/chat-history`),
    generateMicro:    (id) => api.post(`/courses/${id}/generate-micro`),
    generateItem:     (id) => api.post(`/items/${id}/generate`),
    completeItem:     (id) => api.post(`/items/${id}/complete`),
    syncStudyTime:    (id, seconds) => api.post(`/items/${id}/study-time`, { seconds }),
    deleteCourse:     (id) => api.delete(`/courses/${id}`),
    patchCourse:      (id, body) => api.patch(`/courses/${id}`, body),
    uploadCover:      (id, file) => {
        const fd = new FormData();
        fd.append('file', file);
        return api.post(`/courses/${id}/cover`, fd, { headers: { 'Content-Type': 'multipart/form-data' } });
    },

    fetchDailyMicro: (count, courseIds, excludeIds) => {
        let url = `/daily-micro-courses?count=${count}`;
        if (courseIds && courseIds.length) url += `&course_ids=${courseIds.join(',')}`;
        if (excludeIds && excludeIds.length) url += `&exclude_ids=${excludeIds.join(',')}`;
        return api.get(url);
    },

    saveSettings:    (data) => api.post('/settings', data),
    generateInsight: ()     => api.post('/generate-insight'),
    rebuildProfile:  ()     => api.post('/profile/rebuild'),

    chatCourseGen: (messages) => api.post('/chat/course-generator', { messages }),

    coachStream: async (courseId, itemId, message, onChunk) => {
        const res = await fetch(`${API_BASE}/chat/coach`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
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
