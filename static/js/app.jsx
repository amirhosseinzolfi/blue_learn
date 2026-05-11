const { useState, useEffect, useRef } = React;
const {
    Plus, BookOpen, CheckCircle, ChevronLeft, ChevronRight,
    Play, Layout, Trophy, Loader2, MoreVertical, Trash2,
    Edit2, Copy, RefreshCw, Send, Bot, User, X,
    Maximize, Minimize, Clock, Sparkles, BarChart, Settings, Zap,
    Palette, Image
} = window.Icons;

const API_BASE = window.location.origin;

const COURSE_COLORS = [
    { name: 'purple', label: 'بنفش', hex: '#a855f7', classes: { border: 'border-purple-900/20', hoverBorder: 'hover:border-purple-500/40', text: 'text-primary', hoverText: 'group-hover:text-primary', from: 'from-primary', to: 'to-indigo-500', bgLight: 'bg-primary/20', shadowHover: 'hover:shadow-[0_0_30px_rgba(168,85,247,0.15)]', dropShadow: 'drop-shadow-[0_0_8px_rgba(168,85,247,0.5)]', glow: 'bg-primary/10' } },
    { name: 'blue', label: 'آبی', hex: '#3b82f6', classes: { border: 'border-blue-900/20', hoverBorder: 'hover:border-blue-500/40', text: 'text-blue-500', hoverText: 'group-hover:text-blue-500', from: 'from-blue-500', to: 'to-cyan-500', bgLight: 'bg-blue-500/20', shadowHover: 'hover:shadow-[0_0_30px_rgba(59,130,246,0.15)]', dropShadow: 'drop-shadow-[0_0_8px_rgba(59,130,246,0.5)]', glow: 'bg-blue-500/10' } },
    { name: 'emerald', label: 'زمردی', hex: '#10b981', classes: { border: 'border-emerald-900/20', hoverBorder: 'hover:border-emerald-500/40', text: 'text-emerald-500', hoverText: 'group-hover:text-emerald-500', from: 'from-emerald-500', to: 'to-teal-500', bgLight: 'bg-emerald-500/20', shadowHover: 'hover:shadow-[0_0_30px_rgba(16,185,129,0.15)]', dropShadow: 'drop-shadow-[0_0_8px_rgba(16,185,129,0.5)]', glow: 'bg-emerald-500/10' } },
    { name: 'rose', label: 'قرمز', hex: '#f43f5e', classes: { border: 'border-rose-900/20', hoverBorder: 'hover:border-rose-500/40', text: 'text-rose-500', hoverText: 'group-hover:text-rose-500', from: 'from-rose-500', to: 'to-orange-500', bgLight: 'bg-rose-500/20', shadowHover: 'hover:shadow-[0_0_30px_rgba(244,63,94,0.15)]', dropShadow: 'drop-shadow-[0_0_8px_rgba(244,63,94,0.5)]', glow: 'bg-rose-500/10' } },
    { name: 'amber', label: 'کهربایی', hex: '#f59e0b', classes: { border: 'border-amber-900/20', hoverBorder: 'hover:border-amber-500/40', text: 'text-amber-500', hoverText: 'group-hover:text-amber-500', from: 'from-amber-500', to: 'to-yellow-500', bgLight: 'bg-amber-500/20', shadowHover: 'hover:shadow-[0_0_30px_rgba(245,158,11,0.15)]', dropShadow: 'drop-shadow-[0_0_8px_rgba(245,158,11,0.5)]', glow: 'bg-amber-500/10' } },
    { name: 'cyan', label: 'فیروزه‌ای', hex: '#06b6d4', classes: { border: 'border-cyan-900/20', hoverBorder: 'hover:border-cyan-500/40', text: 'text-cyan-500', hoverText: 'group-hover:text-cyan-500', from: 'from-cyan-500', to: 'to-blue-500', bgLight: 'bg-cyan-500/20', shadowHover: 'hover:shadow-[0_0_30px_rgba(6,182,212,0.15)]', dropShadow: 'drop-shadow-[0_0_8px_rgba(6,182,212,0.5)]', glow: 'bg-cyan-500/10' } }
];

const getCourseColor = (name) => COURSE_COLORS.find(c => c.name === name) || COURSE_COLORS[0];

const isEnglish = (text) => {
    if (!text) return false;
    // Count English vs non-English characters (Persian/Arabic range)
    const englishChars = (text.match(/[a-zA-Z]/g) || []).length;
    const farsiChars = (text.match(/[\u0600-\u06FF]/g) || []).length;
    // If it's mostly English characters, or if it has any English and no Farsi
    return englishChars > farsiChars;
};

function App() {
    // --- State Management ---
    const [courses, setCourses] = useState([]);
    const [currentView, setCurrentView] = useState('courses');
    const [dailyMicroCourses, setDailyMicroCourses] = useState([]);
    const [settings, setSettings] = useState({ google_api_key: '', model_name: '' });
    const [settingsSaved, setSettingsSaved] = useState(false);
    const [selectedCourse, setSelectedCourse] = useState(null);
    const [loading, setLoading] = useState(false);
    const [viewingItem, setViewingItem] = useState(null);
    const [activeMenu, setActiveMenu] = useState(null);
    const [isChatModalOpen, setIsChatModalOpen] = useState(false);
    const [chatMessages, setChatMessages] = useState([]);
    const [chatInput, setChatInput] = useState('');
    const [isChatLoading, setIsChatLoading] = useState(false);
    const [pendingCourseData, setPendingCourseData] = useState(null);
    const [isSidebarOpen, setIsSidebarOpen] = useState(true);
    const [loadingItemId, setLoadingItemId] = useState(null);
    const [copied, setCopied] = useState(false);
    const [isSessionMenuOpen, setIsSessionMenuOpen] = useState(false);
    const [isCoachMode, setIsCoachMode] = useState(false);
    const [isCoachFullScreen, setIsCoachFullScreen] = useState(false);
    const [coachMessages, setCoachMessages] = useState([]);
    const [coachInput, setCoachInput] = useState('');
    const [isCoachLoading, setIsCoachLoading] = useState(false);
    const [sidebarRatio, setSidebarRatio] = useState(33);
    const [isDragging, setIsDragging] = useState(false);
    const [openChapters, setOpenChapters] = useState({});
    const mainScrollRef = useRef(null);
    
    // --- Course Settings State ---
    const [isCourseSettingsModalOpen, setIsCourseSettingsModalOpen] = useState(false);
    const [editingCourse, setEditingCourse] = useState(null);
    const [courseSettingsForm, setCourseSettingsForm] = useState({ title: '', color: 'purple', cover_image: null, preview_image: null });
    const coverImageInputRef = useRef(null);
    
    // --- Daily Micro Course Enhancements ---
    const [microSettings, setMicroSettings] = useState(() => {
        const saved = localStorage.getItem('micro_settings');
        return saved ? JSON.parse(saved) : { courseIds: [], countPerCourse: 1 };
    });
    const [isMicroSettingsOpen, setIsMicroSettingsOpen] = useState(false);
    const [isDailyLoading, setIsDailyLoading] = useState(false);
    const [toast, setToast] = useState(null);

    const showToast = (message, type = 'success') => {
        setToast({ message, type });
        setTimeout(() => setToast(null), 4000);
    };

    // --- Refs ---
    const menuRef = useRef(null);
    const coachScrollRef = useRef(null);
    const chatScrollRef = useRef(null);
    const contentRef = useRef(null);
    const sessionMenuRef = useRef(null);

    // --- Effects ---

    // Sidebar Dragging Logic
    useEffect(() => {
        const handleMouseMove = (e) => {
            if (!isDragging) return;
            const container = contentRef.current;
            if (!container) return;
            const rect = container.getBoundingClientRect();
            const newWidthPx = e.clientX - rect.left;
            const percentage = (newWidthPx / rect.width) * 100;
            if (percentage > 20 && percentage < 50) {
                setSidebarRatio(percentage);
            }
        };
        const handleMouseUp = () => setIsDragging(false);

        if (isDragging) {
            document.addEventListener('mousemove', handleMouseMove);
            document.addEventListener('mouseup', handleMouseUp);
            document.body.style.userSelect = 'none';
        } else {
            document.body.style.userSelect = 'auto';
        }

        return () => {
            document.removeEventListener('mousemove', handleMouseMove);
            document.removeEventListener('mouseup', handleMouseUp);
        };
    }, [isDragging]);

    // Initial Load & Outside Clicks
    useEffect(() => {
        fetchCourses();
        
        const todayKey = new Date().toISOString().split('T')[0];
        const storageKey = `daily_courses_${todayKey}`;
        const stored = localStorage.getItem(storageKey);
        
        if (stored) {
            setDailyMicroCourses(JSON.parse(stored));
        } else {
            fetchDailyMicroCourses(false, microSettings);
        }
        
        fetchSettings();
        const handleClickOutside = (event) => {
            if (menuRef.current && !menuRef.current.contains(event.target)) {
                setActiveMenu(null);
            }
            if (sessionMenuRef.current && !sessionMenuRef.current.contains(event.target)) {
                setIsSessionMenuOpen(false);
            }
        };
        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    // Item Viewing Effects
    useEffect(() => {
        if (viewingItem && contentRef.current) {
            window.scrollTo({ top: contentRef.current.offsetTop - 20, behavior: 'smooth' });
        }
        if (viewingItem) {
            setIsCoachMode(false);
            if (viewingItem.chapter) {
                setOpenChapters(prev => ({ ...prev, [viewingItem.chapter]: true }));
            }
            // Persist the last viewed session ID for this course
            if (selectedCourse) {
                localStorage.setItem(`last_session_${selectedCourse.id}`, viewingItem.id);
            }
        }
    }, [viewingItem]);

    // Sync daily micro courses with courses completion status
    useEffect(() => {
        if (courses.length > 0 && dailyMicroCourses.length > 0) {
            let changed = false;
            const updated = dailyMicroCourses.map(daily => {
                const course = courses.find(c => c.id === daily.course_id);
                if (course) {
                    const item = course.items.find(i => i.id === daily.item_id);
                    if (item && item.is_completed !== daily.is_completed) {
                        changed = true;
                        return { ...daily, is_completed: item.is_completed };
                    }
                }
                return daily;
            });
            if (changed) {
                setDailyMicroCourses(updated);
                const todayKey = new Date().toISOString().split('T')[0];
                localStorage.setItem(`daily_courses_${todayKey}`, JSON.stringify(updated));
            }
        }
    }, [courses]);

    const scrollToCoachBottom = () => {
        setTimeout(() => {
            if (coachScrollRef.current) coachScrollRef.current.scrollTop = coachScrollRef.current.scrollHeight;
        }, 50);
    };

    useEffect(() => {
        if (isCoachMode) {
            scrollToCoachBottom();
        }
    }, [isCoachMode]);

    useEffect(() => {
        if (chatScrollRef.current) chatScrollRef.current.scrollTop = chatScrollRef.current.scrollHeight;
    }, [chatMessages, isChatLoading]);

    // --- API Interactions ---

    const fetchCourses = async () => {
        try {
            const res = await axios.get(`${API_BASE}/courses/`);
            setCourses(res.data);
        } catch (err) {
            console.error("Error fetching courses", err);
        }
    };

    const fetchDailyMicroCourses = async (isLoadMore = false, settingsOverride = null) => {
        const settingsToUse = settingsOverride || microSettings;
        setIsDailyLoading(true);
        try {
            let url = `${API_BASE}/daily-micro-courses?count=${settingsToUse.countPerCourse}`;
            if (settingsToUse.courseIds && settingsToUse.courseIds.length > 0) {
                url += `&course_ids=${settingsToUse.courseIds.join(',')}`;
            }
            if (isLoadMore && dailyMicroCourses.length > 0) {
                const excludeIds = dailyMicroCourses.map(i => i.item_id).join(',');
                url += `&exclude_ids=${excludeIds}`;
            }
            
            const res = await axios.get(url);
            
            const todayKey = new Date().toISOString().split('T')[0];
            const storageKey = `daily_courses_${todayKey}`;
            
            if (isLoadMore) {
                setDailyMicroCourses(prev => {
                    const newItems = [...prev, ...res.data];
                    const uniqueItems = Array.from(new Map(newItems.map(item => [item.item_id, item])).values());
                    localStorage.setItem(storageKey, JSON.stringify(uniqueItems));
                    return uniqueItems;
                });
            } else {
                setDailyMicroCourses(res.data);
                localStorage.setItem(storageKey, JSON.stringify(res.data));
            }
        } catch (err) {
            console.error("Error fetching daily micro courses", err);
        } finally {
            setIsDailyLoading(false);
        }
    };
    
    const loadMoreDaily = () => {
        fetchDailyMicroCourses(true);
    };

    const fetchSettings = async () => {
        try {
            const res = await axios.get(`${API_BASE}/settings`);
            setSettings({
                google_api_key: res.data.google_api_key || '',
                model_name: res.data.model_name || 'gemini-flash-latest'
            });
        } catch (err) {
            console.error("Error fetching settings", err);
        }
    };

    const saveSettings = async (e) => {
        e.preventDefault();
        try {
            await axios.post(`${API_BASE}/settings`, settings);
            setSettingsSaved(true);
            setTimeout(() => setSettingsSaved(false), 3000);
        } catch (err) {
            console.error("Error saving settings", err);
        }
    };

    const createCourse = async (courseData) => {
        setLoading(true);
        try {
            const res = await axios.post(`${API_BASE}/courses/`, courseData);
            fetchCourses();
            return res.data;
        } catch (err) {
            console.error("Error creating course", err);
            return null;
        } finally {
            setLoading(false);
        }
    };

    const sendChatMessage = async () => {
        if (!chatInput.trim() || isChatLoading) return;
        const newMessages = [...chatMessages, { role: 'user', content: chatInput }];
        setChatMessages(newMessages);
        setChatInput('');
        setIsChatLoading(true);
        setPendingCourseData(null);

        try {
            const res = await axios.post(`${API_BASE}/chat/course-generator`, { messages: newMessages });
            const data = res.data;

            setChatMessages(prev => [...prev, { role: 'assistant', content: data.chat_response }]);
            if (data.is_complete && data.course_data) {
                setPendingCourseData(data.course_data);
            }
        } catch (err) {
            console.error("Error in chat", err);
            setChatMessages(prev => [...prev, { role: 'assistant', content: 'خطایی رخ داد. لطفا دوباره تلاش کنید.' }]);
        } finally {
            setIsChatLoading(false);
        }
    };

    const handleAcceptCourse = async () => {
        if (!pendingCourseData) return;
        setChatMessages(prev => [...prev, { role: 'assistant', content: 'در حال ایجاد دوره...' }]);
        const newCourse = await createCourse(pendingCourseData);
        setIsChatModalOpen(false);
        setPendingCourseData(null);
        if (newCourse && newCourse.id) {
            // Navigate to the new course's outline page (not viewing any item)
            setViewingItem(null);
            setLoading(true);
            try {
                const res = await axios.get(`${API_BASE}/courses/${newCourse.id}`);
                setSelectedCourse(res.data);
            } catch (err) {
                console.error("Error fetching new course", err);
            } finally {
                setLoading(false);
            }
        }
    };

    const sendCoachMessage = async () => {
        if (!coachInput.trim() || isCoachLoading || !selectedCourse || !viewingItem) return;
        const newMessages = [...coachMessages, { role: 'user', content: coachInput }];
        setCoachMessages(newMessages);
        scrollToCoachBottom();
        setCoachInput('');
        setIsCoachLoading(true);

        try {
            const response = await fetch(`${API_BASE}/chat/coach`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    message: coachInput,
                    course_id: selectedCourse.id,
                    item_id: viewingItem.id
                })
            });
            if (!response.ok) throw new Error("Network response was not ok");

            const reader = response.body.getReader();
            const decoder = new TextDecoder("utf-8");
            let done = false;
            let assistantMessage = "";
            let isFirstChunk = true;

            while (!done) {
                const { value, done: readerDone } = await reader.read();
                done = readerDone;
                if (value) {
                    const chunk = decoder.decode(value, { stream: true });
                    assistantMessage += chunk;

                    if (isFirstChunk) {
                        setIsCoachLoading(false);
                        setCoachMessages(prev => [...prev, { role: 'assistant', content: assistantMessage }]);
                        isFirstChunk = false;
                    } else {
                        setCoachMessages(prev => {
                            const newMsgs = [...prev];
                            newMsgs[newMsgs.length - 1].content = assistantMessage;
                            return newMsgs;
                        });
                    }
                }
            }
        } catch (err) {
            console.error("Error in coach chat", err);
            setCoachMessages(prev => [...prev, { role: 'assistant', content: 'خطایی رخ داد. لطفا دوباره تلاش کنید.' }]);
        } finally {
            setIsCoachLoading(false);
        }
    };

    const handleSaveCourseSettings = async (e) => {
        e.preventDefault();
        if (!editingCourse) return;
        setLoading(true);
        try {
            await axios.patch(`${API_BASE}/courses/${editingCourse.id}`, {
                title: courseSettingsForm.title,
                color: courseSettingsForm.color
            });

            if (courseSettingsForm.cover_image) {
                const formData = new FormData();
                formData.append('file', courseSettingsForm.cover_image);
                await axios.post(`${API_BASE}/courses/${editingCourse.id}/cover`, formData, {
                    headers: { 'Content-Type': 'multipart/form-data' }
                });
            }
            
            fetchCourses();
            if (selectedCourse && selectedCourse.id === editingCourse.id) {
                const res = await axios.get(`${API_BASE}/courses/${editingCourse.id}`);
                setSelectedCourse(res.data);
            }
            setIsCourseSettingsModalOpen(false);
            setEditingCourse(null);
        } catch (err) {
            console.error("Error saving course settings", err);
        } finally {
            setLoading(false);
        }
    };

    const deleteCourseAction = async (id, e) => {
        e.stopPropagation();
        if (!confirm('آیا از حذف این دوره اطمینان دارید؟')) return;
        try {
            await axios.delete(`${API_BASE}/courses/${id}`);
            fetchCourses();
            setActiveMenu(null);
        } catch (err) {
            console.error("Error deleting course", err);
        }
    };



    const selectCourse = async (courseId, keepViewingItem = false) => {
        setLoading(true);
        try {
            const res = await axios.get(`${API_BASE}/courses/${courseId}`);
            setSelectedCourse(res.data);
            
            // Scroll to top of main content when selecting a new course
            if (!keepViewingItem && mainScrollRef.current) {
                mainScrollRef.current.scrollTo(0, 0);
            }

            // Load chat history for the course
            try {
                const historyRes = await axios.get(`${API_BASE}/courses/${courseId}/chat-history`);
                if (historyRes.data && historyRes.data.length > 0) {
                    setCoachMessages(historyRes.data);
                    if (isCoachMode) scrollToCoachBottom();
                } else {
                    setCoachMessages([{ role: 'assistant', content: `سلام! من دستیار هوشمند شما برای این دوره هستم. اگر سوالی دارید یا بخشی برایتان نامفهوم است، بپرسید.` }]);
                }
            } catch (historyErr) {
                console.error("Error fetching course chat history", historyErr);
                setCoachMessages([{ role: 'assistant', content: `سلام! من دستیار هوشمند شما برای این دوره هستم.` }]);
            }

            if (!keepViewingItem) {
                // When opening a course from the main list, always show the course overview first
                setViewingItem(null);
            }
        } catch (err) {
            console.error("Error fetching course details", err);
        } finally {
            setLoading(false);
        }
    };

    const generateRandomMicro = async () => {
        if (!selectedCourse) return;
        setLoading(true);
        try {
            const res = await axios.post(`${API_BASE}/courses/${selectedCourse.id}/generate-micro`);
            setViewingItem(res.data);
            selectCourse(selectedCourse.id, true);
        } catch (err) {
            console.error("Error generating micro course", err);
        } finally {
            setLoading(false);
        }
    };

    const generateSpecificMicro = async (itemId) => {
        const targetItem = selectedCourse.items.find(i => i.id === itemId);
        if (targetItem) setViewingItem({ ...targetItem, content: null });
        setLoadingItemId(itemId);
        setLoading(true);
        try {
            const res = await axios.post(`${API_BASE}/items/${itemId}/generate`);
            // Immediately show the generated content
            setViewingItem(res.data);
            setLoadingItemId(null);
            // Refresh course data in background without touching viewingItem
            const courseRes = await axios.get(`${API_BASE}/courses/${selectedCourse.id}`);
            setSelectedCourse(courseRes.data);
            // Update viewingItem with the fresh data from the refreshed course
            const updatedItem = courseRes.data.items.find(i => i.id === itemId);
            if (updatedItem) {
                setViewingItem(updatedItem);
            }
        } catch (err) {
            console.error("Error generating item", err);
        } finally {
            setLoadingItemId(null);
            setLoading(false);
        }
    };

    const handleMicroCardClick = async (item) => {
        setCurrentView('courses');
        setLoading(true);
        try {
            const res = await axios.get(`${API_BASE}/courses/${item.course_id}`);
            const courseData = res.data;
            setSelectedCourse(courseData);

            try {
                const historyRes = await axios.get(`${API_BASE}/courses/${item.course_id}/chat-history`);
                if (historyRes.data && historyRes.data.length > 0) {
                    setCoachMessages(historyRes.data);
                    if (isCoachMode) scrollToCoachBottom();
                } else {
                    setCoachMessages([{ role: 'assistant', content: `سلام! من دستیار هوشمند شما برای این دوره هستم. اگر سوالی دارید یا بخشی برایتان نامفهوم است، بپرسید.` }]);
                }
            } catch (historyErr) {
                setCoachMessages([{ role: 'assistant', content: `سلام! من دستیار هوشمند شما برای این دوره هستم.` }]);
            }

            const targetItem = courseData.items.find(i => i.id === item.item_id);
            if (targetItem) {
                if (targetItem.content) {
                    setViewingItem(targetItem);
                } else {
                    setViewingItem({ ...targetItem, content: null });
                    setLoadingItemId(targetItem.id);
                    try {
                        const genRes = await axios.post(`${API_BASE}/items/${targetItem.id}/generate`);
                        setViewingItem(genRes.data);
                        const updatedCourseRes = await axios.get(`${API_BASE}/courses/${item.course_id}`);
                        setSelectedCourse(updatedCourseRes.data);
                        const finalUpdatedItem = updatedCourseRes.data.items.find(i => i.id === targetItem.id);
                        if (finalUpdatedItem) setViewingItem(finalUpdatedItem);
                    } catch (err) {
                        console.error("Error generating item", err);
                    } finally {
                        setLoadingItemId(null);
                    }
                }
            }
        } catch (err) {
            console.error("Error handling micro card click", err);
        } finally {
            setLoading(false);
        }
    };

    const completeItem = async (itemId) => {
        try {
            await axios.post(`${API_BASE}/items/${itemId}/complete`);
            if (viewingItem && viewingItem.id === itemId) {
                setViewingItem({ ...viewingItem, is_completed: true });
                showToast('تبریک! این درس با موفقیت به پایان رسید.');
            }
            selectCourse(selectedCourse.id, true);
            setDailyMicroCourses(prev => {
                const updated = prev.map(item => item.item_id === itemId ? { ...item, is_completed: true } : item);
                const todayKey = new Date().toISOString().split('T')[0];
                localStorage.setItem(`daily_courses_${todayKey}`, JSON.stringify(updated));
                return updated;
            });
        } catch (err) {
            console.error("Error completing item", err);
        }
    };

    const copyToClipboard = () => {
        if (viewingItem && viewingItem.content) {
            navigator.clipboard.writeText(viewingItem.content);
            setCopied(true);
            setTimeout(() => setCopied(false), 2000);
        }
    };

    // --- Helper Calculations ---
    const currentIndex = (selectedCourse && viewingItem) ? selectedCourse.items.findIndex(i => i.id === viewingItem.id) : -1;
    const prevItem = currentIndex > 0 ? selectedCourse.items[currentIndex - 1] : null;
    const nextItem = (currentIndex !== -1 && currentIndex < selectedCourse.items.length - 1) ? selectedCourse.items[currentIndex + 1] : null;

    return (
        <div className="min-h-screen bg-dark text-slate-200 relative overflow-clip flex flex-col md:flex-row">
            {/* Toast Notification */}
            {toast && (
                <div className="fixed top-8 left-1/2 -translate-x-1/2 z-[100] animate-in fade-in slide-in-from-top-4 duration-500">
                    <div className="bg-dark-lightest/80 backdrop-blur-xl border border-green-500/30 px-6 py-4 rounded-2xl shadow-[0_20px_40px_-10px_rgba(0,0,0,0.5)] flex items-center gap-4">
                        <div className="w-10 h-10 bg-green-500/20 rounded-xl flex items-center justify-center text-green-400 shadow-[0_0_15px_rgba(34,197,94,0.2)]">
                            <CheckCircle size={24} />
                        </div>
                        <div className="text-right">
                            <p className="text-white font-bold text-sm">{toast.message}</p>
                        </div>
                    </div>
                </div>
            )}

            {/* Background glow effects */}
            <div className="absolute top-0 left-0 w-full h-full overflow-hidden -z-10 pointer-events-none">
                <div className="absolute top-[-10%] right-[-5%] w-96 h-96 bg-primary/20 blur-[100px] rounded-full"></div>
                <div className="absolute bottom-[-10%] left-[-10%] w-[30rem] h-[30rem] bg-indigo-500/10 blur-[120px] rounded-full"></div>
            </div>

            {/* Sidebar Desktop */}
            <div className="hidden md:block w-[72px] shrink-0 z-50 relative">
                <aside className="group fixed top-[110px] bottom-[110px] right-4 w-[72px] hover:w-[218px] bg-dark-lighter/95 backdrop-blur-xl border border-white/[0.06] flex flex-col shadow-[0_8px_40px_rgba(0,0,0,0.6),inset_0_1px_0_rgba(255,255,255,0.04)] rounded-[1.75rem] transition-[width] duration-300 ease-[cubic-bezier(0.4,0,0.2,1)] overflow-hidden">

                    {/* Logo */}
                    <div className="flex items-center h-16 px-[18px] shrink-0 border-b border-white/[0.05]">
                        <div className="w-8 h-8 shrink-0 flex items-center justify-center rounded-xl bg-primary/15 border border-primary/20 shadow-[0_0_12px_rgba(168,85,247,0.15)]">
                            <BookOpen className="text-primary" size={15} />
                        </div>
                        <span className="mr-3 text-[15px] font-bold bg-gradient-to-l from-purple-300 to-indigo-300 bg-clip-text text-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-200 whitespace-nowrap tracking-wide">
                            بلو لرن
                        </span>
                    </div>

                    {/* Nav items */}
                    <nav className="flex-1 flex flex-col gap-0.5 p-2 pt-2.5">
                        {[
                            { view: 'courses',  icon: Layout,   label: 'دوره\u200cها' },
                            { view: 'micro',    icon: Zap,      label: 'میکرو دوره\u200cها' },
                            { view: 'settings', icon: Settings, label: 'تنظیمات' },
                        ].map(({ view, icon: Icon, label }) => (
                            <button
                                key={view}
                                onClick={() => { setCurrentView(view); setSelectedCourse(null); }}
                                title={label}
                                className={`relative flex items-center h-10 rounded-xl transition-all duration-200 group/item overflow-hidden
                                    ${currentView === view
                                        ? 'bg-primary/15 text-primary'
                                        : 'text-slate-500 hover:text-slate-200 hover:bg-white/[0.05]'
                                    }`}
                            >
                                {currentView === view && (
                                    <span className="absolute right-0 top-1/2 -translate-y-1/2 w-[3px] h-4 bg-primary rounded-l-full shadow-[0_0_6px_rgba(168,85,247,0.7)]" />
                                )}
                                <span className="flex items-center justify-center w-[52px] shrink-0">
                                    <Icon size={17} className={`transition-transform duration-200 ${currentView === view ? '' : 'group-hover/item:scale-110'}`} />
                                </span>
                                <span className="text-[15px] font-bold opacity-0 group-hover:opacity-100 transition-opacity duration-200 whitespace-nowrap pr-1 leading-none">{label}</span>
                            </button>
                        ))}
                    </nav>

                    {/* New course button */}
                    <div className="p-2 pb-2.5 shrink-0 border-t border-white/[0.04]">
                        <button
                            onClick={() => {
                                setIsChatModalOpen(true);
                                setChatMessages([{ role: 'assistant', content: 'سلام! من بلو هستم، دستیار هوشمند شما برای طراحی دوره\u200cهای آموزشی شخصی\u200cسازی شده. چه موضوعی را دوست دارید یاد بگیرید؟ لطفاً کمی درباره سطح فعلی و هدفتان هم توضیح دهید تا یک دوره بی\u200cنظیر برایتان آماده کنم.' }]);
                                setChatInput('');
                                setPendingCourseData(null);
                            }}
                            title="دوره جدید"
                            className="w-full h-10 flex items-center rounded-xl bg-primary/20 hover:bg-primary/30 border border-primary/25 hover:border-primary/50 text-primary transition-all duration-200 group/btn overflow-hidden"
                        >
                            <span className="flex items-center justify-center w-[52px] shrink-0">
                                <Plus size={17} className="group-hover/btn:rotate-90 transition-transform duration-300" />
                            </span>
                            <span className="text-[15px] font-bold opacity-0 group-hover:opacity-100 transition-opacity duration-200 whitespace-nowrap pr-1">دوره جدید</span>
                        </button>
                    </div>
                </aside>
            </div>

            {/* Mobile Header */}
            <header className="md:hidden flex justify-between items-center px-4 py-2.5 border-b border-white/[0.05] bg-dark-lighter/90 backdrop-blur-xl sticky top-0 z-20">
                <div className="flex items-center gap-2">
                    <div className="w-7 h-7 flex items-center justify-center rounded-lg bg-primary/15 border border-primary/20">
                        <BookOpen size={13} className="text-primary" />
                    </div>
                    <span className="text-sm font-bold bg-gradient-to-l from-purple-300 to-indigo-300 bg-clip-text text-transparent">بلو لرن</span>
                </div>
                <div className="flex items-center gap-1">
                    <div className="flex items-center gap-0.5 bg-dark-lightest/70 p-1 rounded-xl border border-white/[0.05]">
                        {[
                            { view: 'courses',  icon: Layout },
                            { view: 'micro',    icon: Zap },
                            { view: 'settings', icon: Settings },
                        ].map(({ view, icon: Icon }) => (
                            <button
                                key={view}
                                onClick={() => { setCurrentView(view); setSelectedCourse(null); }}
                                className={`p-2 rounded-lg transition-all duration-200 ${
                                    currentView === view
                                        ? 'bg-primary/20 text-primary'
                                        : 'text-slate-500 hover:text-slate-300'
                                }`}
                            >
                                <Icon size={16} />
                            </button>
                        ))}
                    </div>
                    <button
                        onClick={() => {
                            setIsChatModalOpen(true);
                            setChatMessages([{ role: 'assistant', content: 'سلام! من بلو هستم، دستیار هوشمند شما برای طراحی دوره\u200cهای آموزشی شخصی\u200cسازی شده. چه موضوعی را دوست دارید یاد بگیرید؟ لطفاً کمی درباره سطح فعلی و هدفتان هم توضیح دهید تا یک دوره بی\u200cنظیر برایتان آماده کنم.' }]);
                            setChatInput('');
                            setPendingCourseData(null);
                        }}
                        className="mr-1 p-2 rounded-xl text-primary bg-primary/15 hover:bg-primary/25 border border-primary/20 transition-all duration-200"
                    >
                        <Plus size={16} />
                    </button>
                </div>
            </header>

            {/* Main Content Area */}
            <main ref={mainScrollRef} className="flex-1 h-screen overflow-y-auto p-4 md:p-8 relative">
                <div className="max-w-6xl mx-auto pb-12">
                    {currentView === 'courses' && (
                        !selectedCourse ? (
                            <>
                                <h2 className="text-2xl font-bold mb-8 flex items-center gap-3 text-white">
                                    <Layout className="text-primary" size={28} /> دوره‌های شما
                                </h2>
                                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                                    {courses.map(course => {
                                        const cColor = getCourseColor(course.color);
                                        return (
                                        <div
                                            key={course.id}
                                            onClick={() => selectCourse(course.id)}
                                            className={`bg-dark-lighter border ${cColor.classes.border} p-7 rounded-[2rem] cursor-pointer ${cColor.classes.hoverBorder} transition-all duration-300 group relative shadow-lg shadow-black/20 ${cColor.classes.shadowHover}`}
                                        >
                                            {course.cover_image && (
                                                <div className="w-full h-32 md:h-40 rounded-[1.5rem] mb-5 overflow-hidden relative shadow-inner">
                                                    <img src={course.cover_image} alt={course.title} className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-700 ease-out" />
                                                    <div className="absolute inset-0 bg-gradient-to-t from-dark-lighter via-dark-lighter/20 to-transparent"></div>
                                                </div>
                                            )}
                                            <div className="flex justify-between items-start mb-4">
                                                <div className="flex-1">
                                                    <h3 className={`text-xl font-bold ${cColor.classes.hoverText} transition-colors pr-2 text-slate-100 ${isEnglish(course.short_title || course.title) ? 'ltr-content' : ''}`}>{course.short_title || course.title}</h3>
                                                </div>
                                                <div className="flex items-center gap-2 relative z-10">
                                                    <Trophy className={course.progress === 100 ? "text-yellow-500 drop-shadow-[0_0_8px_rgba(234,179,8,0.5)]" : "text-slate-600"} size={22} />
                                                    <div className="relative" ref={activeMenu === course.id ? menuRef : null}>
                                                        <button
                                                            onClick={(e) => { e.stopPropagation(); setActiveMenu(activeMenu === course.id ? null : course.id); }}
                                                            className="text-slate-500 hover:text-white p-1.5 rounded-full hover:bg-dark-lightest transition-colors"
                                                        >
                                                            <MoreVertical size={18} />
                                                        </button>
                                                        {activeMenu === course.id && (
                                                            <div className="absolute left-0 mt-2 w-44 bg-dark-lightest border border-purple-900/30 rounded-2xl shadow-2xl shadow-black/50 z-20 overflow-hidden backdrop-blur-xl">
                                                                <button
                                                                    onClick={(e) => { e.stopPropagation(); setEditingCourse(course); setCourseSettingsForm({ title: course.title, color: course.color || 'purple', cover_image: null, preview_image: course.cover_image }); setIsCourseSettingsModalOpen(true); setActiveMenu(null); }}
                                                                    className="w-full text-right px-4 py-3 text-sm hover:bg-white/5 flex items-center gap-3 text-slate-200 transition-colors"
                                                                >
                                                                    <Settings size={16} className={cColor.classes.text} /> تنظیمات دوره
                                                                </button>
                                                                <button
                                                                    onClick={(e) => deleteCourseAction(course.id, e)}
                                                                    className="w-full text-right px-4 py-3 text-sm hover:bg-red-500/10 flex items-center gap-3 text-red-400 transition-colors"
                                                                >
                                                                    <Trash2 size={16} /> حذف دوره
                                                                </button>
                                                            </div>
                                                        )}
                                                    </div>
                                                </div>
                                            </div>
                                            <div className="w-full bg-dark-lightest/50 h-2 rounded-full overflow-hidden shadow-inner">
                                                <div
                                                    className={`bg-gradient-to-r ${cColor.classes.from} ${cColor.classes.to} h-full transition-all duration-700 ease-out ${cColor.classes.dropShadow}`}
                                                    style={{ width: `${course.progress}%` }}
                                                />
                                            </div>
                                            <div className="flex justify-between items-center mt-3 pr-1">
                                                <p className="text-xs text-slate-400 font-medium">{Math.round(course.progress)}% تکمیل شده</p>
                                                <div className="flex gap-3 text-[10px] text-slate-500 font-medium">
                                                    {course.level && <span className="flex items-center gap-1.5"><BarChart size={12} /> {course.level}</span>}
                                                    {course.sessions && <span className="flex items-center gap-1.5"><BookOpen size={12} /> {course.sessions} درس</span>}
                                                </div>
                                            </div>
                                        </div>
                                    )})}
                                </div>
                            </>
                        ) : (
                            <div className="flex flex-col gap-8">
                                {!viewingItem && (
                                    <div className="relative bg-dark-lighter/60 backdrop-blur-xl border border-purple-900/30 rounded-[2.5rem] mb-10 overflow-hidden shadow-[0_20px_40px_-15px_rgba(0,0,0,0.5)] group flex flex-col">
                                        {(() => {
                                            const sColor = getCourseColor(selectedCourse.color);
                                            return (
                                            <>
                                        <div className="absolute top-0 left-0 w-full h-full overflow-hidden pointer-events-none z-0">
                                            <div className={`absolute -top-20 -left-20 w-64 h-64 ${sColor.classes.glow} rounded-full blur-[80px] transition-all duration-700`}></div>
                                            <div className={`absolute -bottom-32 -right-32 w-80 h-80 ${sColor.classes.bgLight} rounded-full blur-[100px] transition-all duration-700`}></div>
                                            <Layout size={240} className={`absolute -left-10 top-1/2 -translate-y-1/2 ${sColor.classes.text} opacity-5 -rotate-12`} />
                                        </div>

                                        {selectedCourse.cover_image && (
                                            <div className="w-full h-48 md:h-64 relative border-b border-purple-900/20 shrink-0 z-0">
                                                <img src={selectedCourse.cover_image} alt="" className="w-full h-full object-cover" />
                                                <div className="absolute inset-0 bg-gradient-to-t from-dark-lighter to-transparent"></div>
                                            </div>
                                        )}

                                        <div className="relative z-10 flex flex-col gap-6 p-8 md:p-10">
                                            <div className="flex justify-between items-center w-full">
                                                <button
                                                    onClick={() => setSelectedCourse(null)}
                                                    className="w-fit flex items-center gap-2 text-slate-400 hover:text-white transition-all group/back text-sm font-bold bg-dark-lightest/50 px-4 py-2 rounded-xl border border-purple-900/20 hover:bg-dark-lightest"
                                                >
                                                    <ChevronRight size={18} className="group-hover/back:translate-x-1 transition-transform" /> بازگشت به دوره‌ها
                                                </button>
                                                <button
                                                    onClick={(e) => { e.stopPropagation(); setEditingCourse(selectedCourse); setCourseSettingsForm({ title: selectedCourse.title, color: selectedCourse.color || 'purple', cover_image: null, preview_image: selectedCourse.cover_image }); setIsCourseSettingsModalOpen(true); }}
                                                    className={`p-2.5 flex items-center justify-center text-slate-400 hover:text-white transition-all bg-dark-lightest/50 rounded-xl border border-purple-900/20 hover:bg-dark-lightest ${sColor.classes.hoverBorder}`}
                                                    title="تنظیمات دوره"
                                                >
                                                    <Settings size={20} className={sColor.classes.text} />
                                                </button>
                                            </div>
                                            
                                            <div>
                                                <h2 className={`text-3xl md:text-4xl font-bold text-white mb-4 tracking-tight ${isEnglish(selectedCourse.short_title || selectedCourse.title) ? 'ltr-content' : ''}`}>
                                                    {selectedCourse.short_title || selectedCourse.title}
                                                </h2>
                                                <p className={`text-slate-300 text-sm md:text-base leading-relaxed max-w-4xl opacity-90 ${isEnglish(selectedCourse.description) ? 'ltr-content' : ''}`}>
                                                    {selectedCourse.description}
                                                </p>
                                            </div>

                                            <div className="flex flex-wrap items-center gap-4 mt-2">
                                                {selectedCourse.level && (
                                                    <div className="flex items-center gap-2 bg-dark-lightest/80 px-4 py-2 rounded-2xl border border-purple-900/20 shadow-inner">
                                                        <BarChart size={18} className={sColor.classes.text} /> 
                                                        <span className="text-sm font-bold text-slate-200">سطح: <span className="text-white font-normal">{selectedCourse.level}</span></span>
                                                    </div>
                                                )}
                                                {selectedCourse.hours && (
                                                    <div className="flex items-center gap-2 bg-dark-lightest/80 px-4 py-2 rounded-2xl border border-purple-900/20 shadow-inner">
                                                        <Clock size={18} className={sColor.classes.text} /> 
                                                        <span className="text-sm font-bold text-slate-200">زمان: <span className="text-white font-normal">{selectedCourse.hours} ساعت</span></span>
                                                    </div>
                                                )}
                                                {selectedCourse.sessions && (
                                                    <div className="flex items-center gap-2 bg-dark-lightest/80 px-4 py-2 rounded-2xl border border-purple-900/20 shadow-inner">
                                                        <BookOpen size={18} className={sColor.classes.text} /> 
                                                        <span className="text-sm font-bold text-slate-200">تعداد دروس: <span className="text-white font-normal">{selectedCourse.sessions} درس</span></span>
                                                    </div>
                                                )}
                                            </div>

                                            <div className="mt-6 pt-6 border-t border-purple-900/20">
                                                <div className="flex flex-col sm:flex-row justify-between items-center gap-6">
                                                    <div className="flex-1 w-full">
                                                        <div className="flex justify-between items-center mb-3">
                                                            <span className="text-sm font-bold text-slate-300 flex items-center gap-2">
                                                                <Trophy size={18} className={selectedCourse.progress === 100 ? "text-yellow-500" : sColor.classes.text} />
                                                                میزان تسلط شما
                                                            </span>
                                                            <span className={`text-lg font-bold text-white ${sColor.classes.bgLight} px-3 py-1 rounded-xl border border-purple-900/20 ${sColor.classes.dropShadow}`}>
                                                                {Math.round(selectedCourse.progress)}%
                                                            </span>
                                                        </div>
                                                        <div className="w-full bg-dark-lightest/60 h-4 rounded-full overflow-hidden shadow-inner border border-purple-900/30 relative">
                                                            <div
                                                                className={`bg-gradient-to-r ${sColor.classes.from} ${sColor.classes.to} h-full transition-all duration-1000 ease-out relative`}
                                                                style={{ width: `${selectedCourse.progress}%` }}
                                                            >
                                                                <div className="absolute top-0 right-0 bottom-0 w-20 bg-gradient-to-r from-transparent to-white/30 animate-[shimmer_2s_infinite]"></div>
                                                            </div>
                                                        </div>
                                                    </div>
                                                    
                                                    {(() => {
                                                        const lastSessionId = localStorage.getItem(`last_session_${selectedCourse.id}`);
                                                        const nextSession = (lastSessionId && selectedCourse.items.find(i => i.id == lastSessionId)) || selectedCourse.items.find(i => !i.is_completed);
                                                        if (nextSession) {
                                                            return (
                                                                <button
                                                                    onClick={() => nextSession.content ? setViewingItem(nextSession) : generateSpecificMicro(nextSession.id)}
                                                                    className={`w-full sm:w-auto mt-4 sm:mt-0 bg-gradient-to-r ${sColor.classes.from} ${sColor.classes.to} text-white px-8 py-3.5 rounded-2xl flex items-center justify-center gap-3 font-bold ${sColor.classes.shadowHover} transition-all flex-shrink-0 group/continue`}
                                                                >
                                                                    <Play fill="currentColor" size={18} className="rotate-180 group-hover/continue:scale-110 transition-transform" /> 
                                                                    ادامه یادگیری
                                                                </button>
                                                            );
                                                        } else {
                                                            return (
                                                                <div className="w-full sm:w-auto mt-4 sm:mt-0 bg-yellow-500/20 text-yellow-500 border border-yellow-500/30 px-8 py-3.5 rounded-2xl flex items-center justify-center gap-3 font-bold shadow-[0_0_20px_rgba(234,179,8,0.2)] flex-shrink-0">
                                                                    <CheckCircle size={18} />
                                                                    دوره تکمیل شد
                                                                </div>
                                                            );
                                                        }
                                                    })()}
                                                </div>
                                            </div>
                                        </div>
                                        </>
                                        );
                                        })()}
                                    </div>
                                )}

                                {viewingItem ? (() => {
                                    const vColor = getCourseColor(selectedCourse.color);
                                    return (
                                    <div className="flex flex-col-reverse lg:flex-row gap-3 relative items-start w-full" ref={contentRef}>
                                        <div
                                            className={`bg-dark-lighter border ${vColor.classes.border} rounded-[2rem] p-6 md:p-10 shadow-[0_0_40px_rgba(0,0,0,0.5)] min-h-[60vh]`}
                                            style={{
                                                width: isSidebarOpen ? (window.innerWidth >= 1024 ? `${100 - sidebarRatio}%` : '100%') : '100%',
                                                transition: isDragging ? 'none' : 'width 0.3s ease-in-out'
                                            }}
                                        >
                                            <div className="flex items-center justify-between gap-4 mb-8">
                                                <button onClick={() => setViewingItem(null)} className="w-10 h-10 rounded-full bg-dark-lightest flex items-center justify-center text-slate-400 hover:text-white transition-colors" title="بازگشت به سرفصل‌ها">
                                                    <ChevronRight size={20} />
                                                </button>
                                                {viewingItem.content && (
                                                    <div className="relative" ref={sessionMenuRef}>
                                                        <button
                                                            onClick={() => setIsSessionMenuOpen(!isSessionMenuOpen)}
                                                            className={`w-10 h-10 rounded-full flex items-center justify-center transition-all ${isSessionMenuOpen ? 'bg-dark-lightest text-white' : 'text-slate-400 hover:text-white hover:bg-dark-lightest'}`}
                                                            title="گزینه‌ها"
                                                        >
                                                            <MoreVertical size={20} />
                                                        </button>

                                                        {isSessionMenuOpen && (
                                                            <div className="absolute left-0 top-full mt-2 w-48 bg-dark-lightest border border-purple-900/30 rounded-2xl shadow-2xl shadow-black/50 z-20 overflow-hidden backdrop-blur-xl">
                                                                <button
                                                                    onClick={() => { copyToClipboard(); setIsSessionMenuOpen(false); }}
                                                                    className="w-full text-right px-4 py-3 text-sm hover:bg-white/5 flex items-center gap-3 text-slate-200 transition-colors"
                                                                >
                                                                    {copied ? <CheckCircle size={16} className="text-green-500" /> : <Copy size={16} className="text-slate-400" />}
                                                                    {copied ? 'کپی شد' : 'کپی متن درس'}
                                                                </button>
                                                                <button
                                                                    onClick={() => { generateSpecificMicro(viewingItem.id); setIsSessionMenuOpen(false); }}
                                                                    className="w-full text-right px-4 py-3 text-sm hover:bg-white/5 flex items-center gap-3 text-primary transition-colors border-t border-purple-900/20"
                                                                >
                                                                    <RefreshCw size={16} /> تولید مجدد درس
                                                                </button>
                                                            </div>
                                                        )}
                                                    </div>
                                                )}
                                            </div>
                                            <h3 className={`text-2xl md:text-3xl font-bold mb-8 text-white drop-shadow-[0_0_10px_rgba(255,255,255,0.1)] ${isEnglish(viewingItem.title) ? 'ltr-content' : ''}`}>{viewingItem.title}</h3>

                                            {(!viewingItem.content || loadingItemId === viewingItem.id) ? (
                                                <div className="flex flex-col items-center justify-center py-20 text-center">
                                                    <div className="relative w-20 h-20 mb-6">
                                                        <div className="absolute inset-0 border-4 border-purple-900/30 rounded-full"></div>
                                                        <div className="absolute inset-0 border-4 border-primary rounded-full border-t-transparent animate-spin"></div>
                                                        <Bot className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 text-primary" size={24} />
                                                    </div>
                                                    <h4 className="text-xl font-bold text-white mb-2">در حال تالیف این درس...</h4>
                                                    <p className="text-slate-400 max-w-sm">هوش مصنوعی در حال گردآوری بهترین مطالب و طراحی یک تمرین عملی برای شماست.</p>
                                                </div>
                                            ) : (
                                                <>
                                                    <div
                                                        className={`prose prose-invert prose-purple max-w-none prose-pre:bg-dark-lightest prose-pre:border prose-pre:border-purple-900/30 prose-p:text-slate-300 prose-headings:text-white prose-a:text-primary ${isEnglish(viewingItem.content) ? 'ltr-content' : ''}`}
                                                        dangerouslySetInnerHTML={{ __html: marked.parse(viewingItem.content) }}
                                                    />
                                                    {/* Minimal Modern Navigation & Completion */}
                                                    {/* Session Navigation & Completion Stacking */}
                                                    <div className="mt-20 space-y-6">
                                                        {/* Navigation Row */}
                                                        <div className="flex flex-col sm:flex-row items-center justify-between gap-4 pt-10 border-t border-purple-900/10">
                                                            <div className="flex-1 w-full sm:w-auto">
                                                                {prevItem && (
                                                                    <button 
                                                                        onClick={() => prevItem.content ? setViewingItem(prevItem) : generateSpecificMicro(prevItem.id)} 
                                                                        className="group flex items-center gap-3 text-slate-400 hover:text-white transition-all bg-dark-lightest/30 px-4 py-2.5 rounded-xl border border-purple-900/5 hover:border-purple-900/20 w-full sm:w-fit"
                                                                    >
                                                                        <ChevronRight size={18} className="group-hover:-translate-x-1.5 transition-transform text-slate-500" />
                                                                        <span className="text-sm font-bold truncate max-w-[100px] sm:max-w-[200px] md:max-w-none">{prevItem.title}</span>
                                                                    </button>
                                                                )}
                                                            </div>

                                                            <div className="flex-1 w-full sm:w-auto flex justify-end">
                                                                {nextItem && (
                                                                    <button 
                                                                        onClick={() => nextItem.content ? setViewingItem(nextItem) : generateSpecificMicro(nextItem.id)} 
                                                                        className="group flex items-center gap-3 text-slate-400 hover:text-white transition-all bg-dark-lightest/30 px-4 py-2.5 rounded-xl border border-purple-900/5 hover:border-purple-900/20 w-full sm:w-fit"
                                                                    >
                                                                        <span className="text-sm font-bold truncate max-w-[100px] sm:max-w-[200px] md:max-w-none">{nextItem.title}</span>
                                                                        <ChevronLeft size={18} className="group-hover:translate-x-1.5 transition-transform text-slate-500" />
                                                                    </button>
                                                                )}
                                                            </div>
                                                        </div>

                                                        {/* Completion Button - Full Width */}
                                                        <div>
                                                            {!viewingItem.is_completed ? (
                                                                <button
                                                                    onClick={() => completeItem(viewingItem.id)}
                                                                    className="w-full flex items-center justify-center gap-3 bg-gradient-to-r from-green-500/90 to-emerald-600/90 hover:from-green-500 hover:to-emerald-600 text-white py-4 rounded-2xl font-bold shadow-lg shadow-green-900/20 hover:shadow-green-500/40 transition-all group"
                                                                >
                                                                    <CheckCircle size={22} className="group-hover:scale-110 transition-transform" />
                                                                    اتمام این مرحله و تایید یادگیری
                                                                </button>
                                                            ) : (
                                                                <div className="w-full flex items-center justify-center gap-3 bg-green-500/10 border border-green-500/20 text-green-400 py-4 rounded-2xl font-bold">
                                                                    <CheckCircle size={22} />
                                                                    این درس را با موفقیت پشت سر گذاشتید
                                                                </div>
                                                            )}
                                                        </div>
                                                    </div>
                                                </>
                                            )}

                                        </div>

                                        {isSidebarOpen && (
                                            <div
                                                className="w-4 cursor-col-resize hidden lg:flex items-center justify-center group self-stretch z-20 hover:bg-primary/5 transition-all"
                                                onMouseDown={() => setIsDragging(true)}
                                            >
                                                <div className="w-1.5 h-16 bg-primary/40 rounded-full group-hover:bg-primary transition-all opacity-0 group-hover:opacity-100"></div>
                                            </div>
                                        )}

                                        <div
                                            className={`sticky top-8 ${isSidebarOpen ? 'opacity-100' : 'w-0 opacity-0 hidden lg:block'}`}
                                            style={{
                                                width: isSidebarOpen ? (window.innerWidth >= 1024 ? `${sidebarRatio}%` : '100%') : '0%',
                                                transition: isDragging ? 'none' : 'width 0.3s ease-in-out, opacity 0.3s ease-in-out'
                                            }}
                                        >
                                            <div className="bg-dark-lighter border border-purple-900/20 rounded-[2.5rem] p-6 shadow-[0_30px_60px_-15px_rgba(0,0,0,0.7)] h-[calc(100vh-4rem)] flex flex-col relative overflow-hidden">
                                                <div className="flex items-center justify-between mb-6">
                                                    <div className="flex items-center gap-2">
                                                        {viewingItem && (
                                                            <button
                                                                onClick={() => setIsCoachMode(!isCoachMode)}
                                                                className={`flex items-center gap-2.5 h-9 px-4 rounded-full transition-all ${isCoachMode ? 'bg-primary text-white shadow-[0_0_20px_rgba(168,85,247,0.4)]' : 'bg-dark-lightest/50 text-slate-400 hover:text-primary border border-purple-900/20'}`}
                                                                title={isCoachMode ? "بازگشت به سرفصل‌ها" : "دستیار هوشمند"}>
                                                                <Sparkles size={18} className={isCoachMode ? 'animate-pulse' : ''} />
                                                                <span className="text-xs font-bold">هوش مصنوعی</span>
                                                            </button>
                                                        )}
                                                    </div>
                                                    <div className="flex items-center gap-2">
                                                        {isCoachMode && (
                                                            <button
                                                                onClick={() => setIsCoachFullScreen(true)}
                                                                className="w-8 h-8 flex items-center justify-center bg-dark-lightest/50 hover:bg-primary/10 text-slate-400 hover:text-primary rounded-lg transition-all"
                                                                title="تمام صفحه"
                                                            >
                                                                <Maximize size={16} />
                                                            </button>
                                                        )}
                                                        <button onClick={() => setIsSidebarOpen(false)} className="w-8 h-8 flex items-center justify-center bg-dark-lightest/50 hover:bg-red-500/10 text-slate-400 hover:text-red-400 rounded-lg transition-all" title="بستن منو">
                                                            <X size={16} />
                                                        </button>
                                                    </div>
                                                </div>

                                                {!isCoachMode && (
                                                    <div className="mb-8 pb-6 border-b border-purple-900/10">
                                                        <h3 className="text-xl font-bold text-white mb-4 leading-tight">{selectedCourse.short_title || selectedCourse.title}</h3>
                                                        <div className="flex justify-between text-xs mb-2 px-1">
                                                            <span className={`${vColor.classes.text} font-bold`}>{Math.round(selectedCourse.progress)}%</span>
                                                        </div>
                                                        <div className="w-full bg-dark-lightest/50 h-2 rounded-full overflow-hidden shadow-inner">
                                                            <div
                                                                className={`bg-gradient-to-r ${vColor.classes.from} ${vColor.classes.to} h-full transition-all duration-700 ease-out ${vColor.classes.dropShadow}`}
                                                                style={{ width: `${selectedCourse.progress}%` }}
                                                            />
                                                        </div>
                                                    </div>
                                                )}

                                                <div className="flex-1 flex flex-col overflow-hidden relative">
                                                    {isCoachMode ? (
                                                        <div className="flex-1 flex flex-col h-full absolute inset-0">
                                                            <div className="flex-1 overflow-y-auto pr-1 pb-4 space-y-5" ref={coachScrollRef}>
                                                                {coachMessages.map((msg, idx) => (
                                                                    <div key={idx} className={`flex flex-col w-full ${msg.role === 'user' ? 'items-start' : 'items-start'}`}>
                                                                        {msg.role === 'user' ? (
                                                                            <div className="bg-primary/20 text-slate-100 px-4 py-3 rounded-2xl rounded-tr-sm max-w-[90%] border border-primary/20 shadow-sm ml-auto text-sm leading-relaxed">
                                                                                {msg.content}
                                                                            </div>
                                                                        ) : (
                                                                            <div className="text-slate-200 w-full text-sm leading-relaxed py-1 pr-3 border-r-2 border-primary/40">
                                                                                <div dangerouslySetInnerHTML={{ __html: marked.parse(msg.content || '...') }} className={`prose prose-sm prose-invert prose-p:my-1 prose-pre:my-2 prose-pre:p-2 prose-pre:text-[10px] prose-a:text-primary prose-strong:text-white max-w-none ${isEnglish(msg.content) ? 'ltr-content' : ''}`} />
                                                                            </div>
                                                                        )}
                                                                    </div>
                                                                ))}
                                                                {isCoachLoading && (
                                                                    <div className={`flex items-center gap-2 pr-3 border-r-2 ${vColor.classes.border} py-2`}>
                                                                        <Loader2 size={14} className={`${vColor.classes.text} animate-spin`} />
                                                                        <span className="animate-pulse text-xs text-slate-400">در حال فکر کردن...</span>
                                                                    </div>
                                                                )}
                                                            </div>
                                                            <form onSubmit={(e) => { e.preventDefault(); sendCoachMessage(); }} className="mt-4 flex items-center relative">
                                                                <input
                                                                    type="text"
                                                                    value={coachInput}
                                                                    onChange={(e) => setCoachInput(e.target.value)}
                                                                    placeholder="سوال خود را بپرسید..."
                                                                    className="w-full bg-dark-lightest/60 border border-purple-900/30 rounded-2xl py-3.5 pr-5 pl-12 text-sm text-white focus:outline-none focus:border-primary/50 focus:ring-1 focus:ring-primary/20 transition-all placeholder:text-slate-500"
                                                                    disabled={isCoachLoading}
                                                                />
                                                                <button
                                                                    type="submit"
                                                                    disabled={isCoachLoading || !coachInput.trim()}
                                                                    className="absolute left-1.5 w-9 h-9 rounded-xl bg-primary/10 hover:bg-primary text-primary hover:text-white transition-all flex items-center justify-center disabled:opacity-0 disabled:scale-90"
                                                                >
                                                                    <Send size={16} className="rotate-180" />
                                                                </button>
                                                            </form>
                                                        </div>
                                                    ) : (
                                                        <div className="flex-1 flex flex-col gap-2.5 overflow-y-auto pr-1 pb-4 h-full absolute inset-0">
                                                            {(() => {
                                                                const chapters = Object.entries(selectedCourse.items.reduce((acc, item) => {
                                                                    const ch = item.chapter || 'سایر';
                                                                    if (!acc[ch]) acc[ch] = [];
                                                                    acc[ch].push(item);
                                                                    return acc;
                                                                }, {}));
                                                                return chapters.map(([chapter, items], cIdx) => {
                                                                    const isChapterDone = items.every(i => i.is_completed);
                                                                    const isOpen = openChapters[chapter];
                                                                    return (
                                                                        <div key={chapter} className="shrink-0 rounded-2xl overflow-hidden flex flex-col border border-purple-900/15 bg-dark-lightest/30">
                                                                            <div
                                                                                onClick={() => setOpenChapters(prev => ({ ...prev, [chapter]: !prev[chapter] }))}
                                                                                className="p-3.5 px-4 cursor-pointer flex items-center justify-between transition-colors"
                                                                            >
                                                                                <div className="flex items-center gap-3 flex-1 min-w-0">
                                                                                    <span className={`flex items-center justify-center w-6 h-6 text-sm font-bold shrink-0 ${isChapterDone ? 'text-green-400' : vColor.classes.text
                                                                                        }`}>
                                                                                        {isChapterDone ? <CheckCircle size={16} /> : cIdx + 1}
                                                                                    </span>
                                                                                    <span className="font-semibold text-[13px] truncate text-slate-200">{chapter}</span>
                                                                                </div>
                                                                                <ChevronLeft size={14} className={`text-slate-500 shrink-0 transition-transform duration-200 ${isOpen ? '-rotate-90' : ''}`} />
                                                                            </div>
                                                                            {isOpen && (
                                                                                <div className="flex flex-col gap-0.5 px-3 pb-3">
                                                                                    {items.map((item, sIdx) => (
                                                                                        <div
                                                                                            key={item.id}
                                                                                            onClick={() => item.content ? setViewingItem(item) : generateSpecificMicro(item.id)}
                                                                                            className={`py-2.5 px-2.5 rounded-xl text-xs font-medium cursor-pointer transition-all flex items-center gap-2.5 ${item.id === viewingItem.id
                                                                                                ? vColor.classes.text
                                                                                                : 'text-slate-400 hover:text-slate-300 hover:bg-white/[0.04]'
                                                                                                }`}
                                                                                        >
                                                                                            {item.is_completed
                                                                                                ? <CheckCircle size={12} className="text-green-500 shrink-0" />
                                                                                                : <span className={`w-4 text-center text-[10px] font-bold shrink-0 ${item.id === viewingItem.id ? vColor.classes.text
                                                                                                    : 'text-slate-500'
                                                                                                    }`}>{sIdx + 1}</span>
                                                                                            }
                                                                                            <span className="flex-1 leading-relaxed">{item.title}</span>
                                                                                        </div>
                                                                                    ))}
                                                                                </div>
                                                                            )}
                                                                        </div>
                                                                    );
                                                                });
                                                            })()}
                                                        </div>
                                                    )}
                                                </div>
                                            </div>
                                        </div>

                                        {!isSidebarOpen && (
                                            <button
                                                onClick={() => setIsSidebarOpen(true)}
                                                className={`fixed left-0 top-1/2 -translate-y-1/2 bg-dark-lighter border ${vColor.classes.border} border-l-0 p-2 py-6 rounded-r-2xl shadow-[0_0_30px_rgba(0,0,0,0.5)] ${vColor.classes.text} ${vColor.classes.hoverText} hover:${vColor.classes.bgLight} ${vColor.classes.shadowHover} transition-all z-40 group flex items-center justify-center`}
                                                title="نمایش سرفصل‌ها"
                                            >
                                                <ChevronRight size={20} className="group-hover:translate-x-1 transition-transform" />
                                            </button>
                                        )}
                                    </div>
                                    );
                                })() : (
                                    (() => {
                                        const sColor = getCourseColor(selectedCourse.color);
                                        return (
                                    <div className={`bg-dark-lighter border ${sColor.classes.border} rounded-[2rem] p-6 md:p-10 shadow-[0_0_40px_rgba(0,0,0,0.5)]`}>
                                        <h3 className="text-2xl font-bold mb-8 flex items-center gap-3 text-white">
                                            <Layout className={sColor.classes.text} size={28} /> سرفصل‌های دوره
                                        </h3>
                                        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-5">
                                            {selectedCourse.items.map((item, idx) => (
                                                <div
                                                    key={item.id}
                                                    onClick={() => item.content ? setViewingItem(item) : generateSpecificMicro(item.id)}
                                                    className={`p-6 pb-5 rounded-3xl border transition-all cursor-pointer flex flex-col justify-between aspect-square group relative overflow-hidden shadow-lg ${item.is_completed
                                                        ? 'bg-green-500/5 border-green-500/30 shadow-green-900/5'
                                                        : `bg-dark-lightest/10 border-purple-900/20 ${sColor.classes.hoverBorder} ${sColor.classes.shadowHover}`
                                                        }`}
                                                >
                                                    <div className="z-10 flex-1">
                                                        <span className={`text-xs font-mono mb-3 block font-bold tracking-wider ${sColor.classes.text} opacity-70`}>درس {idx + 1}</span>
                                                        <h4 className={`text-lg font-bold leading-tight ${item.is_completed ? 'text-green-400' : 'text-slate-200 group-hover:text-white transition-colors'} ${isEnglish(item.title) ? 'ltr-content' : ''}`}>
                                                            {item.title}
                                                        </h4>
                                                    </div>
                                                    <div className={`flex justify-between items-center z-10 pt-4 mt-auto border-t ${sColor.classes.border}`}>
                                                        <div className="text-[10px] text-slate-500 font-medium truncate max-w-[70%]" title={item.chapter || 'فصل نامشخص'}>
                                                            {item.chapter || 'فصل نامشخص'}
                                                        </div>
                                                        {item.is_completed ? (
                                                            <div className="bg-green-500/20 p-1.5 rounded-full drop-shadow-[0_0_10px_rgba(34,197,94,0.3)]">
                                                                <CheckCircle size={16} className="text-green-500" />
                                                            </div>
                                                        ) : item.content ? (
                                                            <div className={`${sColor.classes.bgLight} px-2.5 py-1 rounded-lg border ${sColor.classes.border} flex items-center gap-1.5 shadow-sm`}>
                                                                <Zap size={11} className={sColor.classes.text} />
                                                                <span className={`text-[10px] font-bold ${sColor.classes.text} uppercase tracking-wide`}>آماده</span>
                                                            </div>
                                                        ) : (
                                                            <div className="p-2 rounded-xl bg-dark-lighter/50 border border-purple-900/10 group-hover:border-purple-900/30 transition-colors">
                                                                <ChevronLeft size={16} className="text-slate-600 group-hover:text-primary transition-colors" />
                                                            </div>
                                                        )}
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                    );
                                    })()
                                )}

                            </div>
                        ))}

                    {currentView === 'micro' && (
                        <div className="bg-dark-lighter border border-purple-900/20 rounded-[2rem] p-6 md:p-10 shadow-[0_0_40px_rgba(0,0,0,0.5)]">
                            <div className="flex justify-between items-center mb-8 relative">
                                <h2 className="text-2xl font-bold flex items-center gap-3 text-white">
                                    <Zap className="text-primary" size={28} /> میکرو دوره‌های روزانه
                                </h2>
                                <div>
                                    <button 
                                        onClick={() => setIsMicroSettingsOpen(!isMicroSettingsOpen)}
                                        className="p-2 flex items-center justify-center text-slate-500 hover:text-white transition-all hover:rotate-90 duration-300"
                                        title="تنظیمات میکرو دوره"
                                    >
                                        <Settings size={24} />
                                    </button>
                                    {isMicroSettingsOpen && (
                                        <div className="absolute left-0 top-full mt-3 w-72 bg-dark-lightest border border-purple-900/30 rounded-2xl shadow-[0_20px_50px_rgba(0,0,0,0.7)] p-5 z-20 backdrop-blur-xl">
                                            <h4 className="text-sm font-bold text-white mb-4 border-b border-purple-900/20 pb-3 flex items-center gap-2">
                                                <Settings size={16} className="text-primary" /> تنظیمات میکرو دوره
                                            </h4>
                                            <div className="mb-5">
                                                <label className="text-xs text-slate-400 block mb-2 font-medium">تعداد درس در هر دوره (روزانه)</label>
                                                <input 
                                                    type="number" 
                                                    min="1" max="10"
                                                    value={microSettings.countPerCourse}
                                                    onChange={(e) => setMicroSettings({...microSettings, countPerCourse: parseInt(e.target.value) || 1})}
                                                    className="w-full bg-dark-lighter border border-purple-900/50 rounded-lg px-4 py-2.5 text-white text-sm focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary/50 transition-all"
                                                />
                                            </div>
                                            <div className="mb-5">
                                                <label className="text-xs text-slate-400 block mb-2 font-medium">دوره‌های فعال برای یادگیری</label>
                                                <div className="max-h-40 overflow-y-auto space-y-2.5 pr-1 custom-scrollbar">
                                                    {courses.map(c => (
                                                        <label key={c.id} className="flex items-center gap-3 text-sm text-slate-300 hover:text-white cursor-pointer group">
                                                            <div className="relative flex items-center">
                                                                <input 
                                                                    type="checkbox" 
                                                                    checked={microSettings.courseIds.length === 0 || microSettings.courseIds.includes(c.id)}
                                                                    onChange={(e) => {
                                                                        let newIds = [...microSettings.courseIds];
                                                                        if (newIds.length === 0) newIds = courses.map(course => course.id); 
                                                                        
                                                                        if (e.target.checked) {
                                                                            if (!newIds.includes(c.id)) newIds.push(c.id);
                                                                        } else {
                                                                            newIds = newIds.filter(id => id !== c.id);
                                                                        }
                                                                        if (newIds.length === courses.length) newIds = [];
                                                                        setMicroSettings({...microSettings, courseIds: newIds});
                                                                    }}
                                                                    className="w-4 h-4 accent-primary rounded border-purple-900/50 cursor-pointer"
                                                                />
                                                            </div>
                                                            <span className="truncate group-hover:text-primary transition-colors">{c.short_title || c.title}</span>
                                                        </label>
                                                    ))}
                                                </div>
                                            </div>
                                            <button 
                                                onClick={async () => {
                                                    localStorage.setItem('micro_settings', JSON.stringify(microSettings));
                                                    setIsMicroSettingsOpen(false);
                                                    await fetchDailyMicroCourses(false, microSettings);
                                                }}
                                                disabled={isDailyLoading}
                                                className="w-full bg-gradient-to-r from-primary to-indigo-600 hover:from-primary-dark hover:to-indigo-700 text-white rounded-xl py-2.5 text-sm font-bold transition-all shadow-[0_0_15px_rgba(168,85,247,0.3)] hover:shadow-[0_0_20px_rgba(168,85,247,0.5)] disabled:opacity-70 flex items-center justify-center gap-2"
                                            >
                                                {isDailyLoading ? <Loader2 size={16} className="animate-spin" /> : 'اعمال و بروزرسانی'}
                                            </button>
                                        </div>
                                    )}
                                </div>
                            </div>
                            
                            {/* Progress Bar */}
                            {dailyMicroCourses.length > 0 && (
                                <div className="mb-10">
                                    <div className="flex justify-between items-center text-xs mb-3 px-1">
                                        <span className="text-slate-300 font-bold tracking-wide">پیشرفت روزانه شما</span>
                                        <div className="bg-primary/20 px-3 py-1 rounded-full border border-primary/30">
                                            <span className="text-primary font-bold">{Math.round((dailyMicroCourses.filter(i => i.is_completed).length / dailyMicroCourses.length) * 100)}%</span>
                                        </div>
                                    </div>
                                    <div className="w-full bg-dark-lightest/70 h-3.5 rounded-full overflow-hidden shadow-inner border border-purple-900/20 relative">
                                        <div
                                            className="bg-gradient-to-r from-primary via-indigo-500 to-purple-500 h-full transition-all duration-1000 ease-out relative"
                                            style={{ width: `${(dailyMicroCourses.filter(i => i.is_completed).length / dailyMicroCourses.length) * 100}%` }}
                                        >
                                            <div className="absolute top-0 right-0 bottom-0 w-20 bg-gradient-to-r from-transparent to-white/30 animate-[shimmer_2s_infinite]"></div>
                                        </div>
                                    </div>
                                    {dailyMicroCourses.length > 0 && dailyMicroCourses.every(i => i.is_completed) && (
                                        <div className="mt-6 p-5 bg-gradient-to-r from-green-500/10 to-emerald-500/10 border border-green-500/30 rounded-2xl flex items-center justify-center gap-4 text-green-400 shadow-[0_0_30px_rgba(34,197,94,0.15)] relative overflow-hidden">
                                            <div className="absolute top-0 left-0 w-full h-full bg-white/5 animate-pulse"></div>
                                            <Trophy size={28} className="drop-shadow-[0_0_10px_rgba(34,197,94,0.5)] z-10" />
                                            <span className="font-bold text-lg z-10">تبریک! شما تمام میکرو دوره‌های امروز را با موفقیت به پایان رساندید!</span>
                                            <Sparkles size={24} className="absolute right-6 top-1/2 -translate-y-1/2 opacity-50 z-10" />
                                            <Sparkles size={16} className="absolute left-6 top-1/3 opacity-30 z-10" />
                                        </div>
                                    )}
                                </div>
                            )}

                            {dailyMicroCourses.length === 0 ? (
                                <div className="text-center py-20 text-slate-400 bg-dark-lightest/20 rounded-3xl border border-dashed border-purple-900/30">
                                    در حال حاضر هیچ درس ناتمامی برای پیشنهاد روزانه وجود ندارد.
                                </div>
                            ) : (
                                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                                    {dailyMicroCourses.map(item => {
                                        const mColor = getCourseColor(item.course_color);
                                        return (
                                        <div
                                            key={item.item_id}
                                            onClick={() => handleMicroCardClick(item)}
                                            className={`relative backdrop-blur-sm border p-8 rounded-[2rem] hover:-translate-y-1.5 transition-all duration-400 cursor-pointer group flex flex-col overflow-hidden min-h-[180px] shadow-lg ${item.is_completed ? 'bg-green-500/5 border-green-500/30 hover:border-green-400/50 hover:shadow-[0_15px_40px_-10px_rgba(34,197,94,0.2)]' : `bg-dark-lightest/30 border-purple-900/20 hover:bg-dark-lightest/50 ${mColor.classes.hoverBorder} ${mColor.classes.shadowHover}`}`}
                                        >
                                            {/* Subtle background glow on hover */}
                                            {!item.is_completed && <div className={`absolute top-0 left-0 w-32 h-32 ${mColor.classes.bgLight} rounded-full blur-3xl -ml-16 -mt-16 group-hover:opacity-40 transition-all duration-500 opacity-20`}></div>}
                                            {item.is_completed && <div className="absolute top-0 left-0 w-32 h-32 bg-green-500/10 rounded-full blur-3xl -ml-16 -mt-16 group-hover:bg-green-500/20 transition-all duration-500"></div>}

                                            <div className="relative z-10 flex-1 flex flex-col">
                                                <div className="flex items-center gap-3 mb-5">
                                                    <div className={`p-2.5 rounded-xl transition-colors ${item.is_completed ? 'bg-green-500/20 group-hover:bg-green-500/30' : `${mColor.classes.bgLight} group-hover:opacity-80`}`}>
                                                        {item.is_completed ? (
                                                            <CheckCircle size={18} className="text-green-500 drop-shadow-[0_0_8px_rgba(34,197,94,0.4)]" />
                                                        ) : (
                                                            <Zap size={18} className={`${mColor.classes.text} drop-shadow-[0_0_8px_rgba(168,85,247,0.4)]`} />
                                                        )}
                                                    </div>
                                                    <span className={`text-xs font-bold uppercase tracking-wider ${item.is_completed ? 'text-green-400/80' : mColor.classes.text}`}>{item.course_title}</span>
                                                </div>
                                                <h3 className={`text-xl font-bold mb-3 transition-colors ${item.is_completed ? 'text-slate-300 group-hover:text-green-300' : 'text-slate-200 group-hover:text-white'} ${isEnglish(item.item_title) ? 'ltr-content' : ''}`}>{item.item_title}</h3>
                                                <div className="mt-auto pt-4 flex items-center justify-between">
                                                    <p className={`text-xs font-medium flex items-center gap-1.5 ${item.is_completed ? 'text-green-500/60' : 'text-slate-500'}`}>
                                                        <Layout size={14} className="opacity-70" /> {item.chapter || 'فصل نامشخص'}
                                                    </p>
                                                    <div className={`opacity-0 -translate-x-4 group-hover:opacity-100 group-hover:translate-x-0 transition-all duration-300 ${item.is_completed ? 'text-green-400' : mColor.classes.text}`}>
                                                        <ChevronLeft size={20} />
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                        );
                                    })}
                                </div>
                            )}
                            
                            {dailyMicroCourses.length > 0 && !dailyMicroCourses.every(i => i.is_completed) && (
                                <div className="mt-10 flex justify-center border-t border-purple-900/20 pt-6">
                                    <button 
                                        onClick={loadMoreDaily}
                                        disabled={isDailyLoading}
                                        className="text-slate-400 hover:text-primary transition-colors text-sm font-medium flex items-center gap-2 group disabled:opacity-50"
                                    >
                                        <span className="bg-dark-lightest/50 p-2 rounded-full group-hover:bg-primary/10 transition-colors">
                                            <RefreshCw size={16} className={`transition-transform duration-500 ${isDailyLoading ? 'animate-spin' : 'group-hover:rotate-180'}`} />
                                        </span>
                                        {isDailyLoading ? 'در حال بارگذاری...' : 'بارگذاری میکرو دوره‌های بیشتر'}
                                    </button>
                                </div>
                            )}
                        </div>
                    )}

                    {currentView === 'settings' && (
                        <div className="max-w-2xl mx-auto">
                            <div className="bg-dark-lighter border border-purple-900/20 rounded-[2rem] p-6 md:p-10 shadow-[0_0_40px_rgba(0,0,0,0.5)]">
                                <h2 className="text-2xl font-bold mb-8 flex items-center gap-3 text-white">
                                    <Settings className="text-primary" size={28} /> تنظیمات سیستم
                                </h2>
                                <form onSubmit={saveSettings} className="space-y-6">
                                    <div>
                                        <label className="block text-sm font-medium text-slate-300 mb-2">Google API Key</label>
                                        <input
                                            type="password"
                                            value={settings.google_api_key}
                                            onChange={(e) => setSettings({ ...settings, google_api_key: e.target.value })}
                                            className="w-full bg-dark-lightest border border-purple-900/50 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary/50 text-left"
                                            placeholder="AIzaSy..."
                                            dir="ltr"
                                        />
                                        <p className="text-xs text-slate-500 mt-2">کلید دسترسی به هوش مصنوعی گوگل</p>
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium text-slate-300 mb-2">مدل Gemini (مثال: gemini-flash-latest)</label>
                                        <input
                                            type="text"
                                            value={settings.model_name}
                                            onChange={(e) => setSettings({ ...settings, model_name: e.target.value })}
                                            className="w-full bg-dark-lightest border border-purple-900/50 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary/50 text-left"
                                            placeholder="gemini-flash-latest"
                                            dir="ltr"
                                        />
                                        <p className="text-xs text-slate-500 mt-2">نام مدل مورد استفاده برای تمامی سرویس‌های سایت</p>
                                    </div>
                                    <div className="pt-4 border-t border-purple-900/30 flex items-center justify-between">
                                        <button
                                            type="submit"
                                            className="bg-gradient-to-r from-primary to-indigo-600 hover:from-primary-dark hover:to-indigo-700 text-white px-8 py-3 rounded-xl font-bold transition-all shadow-[0_0_15px_rgba(168,85,247,0.3)] hover:shadow-[0_0_25px_rgba(168,85,247,0.5)]"
                                        >
                                            ذخیره تنظیمات
                                        </button>
                                        {settingsSaved && (
                                            <span className="text-green-400 text-sm font-medium flex items-center gap-2">
                                                <CheckCircle size={16} /> ذخیره شد!
                                            </span>
                                        )}
                                    </div>
                                </form>
                            </div>
                        </div>
                    )}
                </div>
            </main>

            {/* Blue Chat Modal */}
            {isChatModalOpen && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-dark/95 backdrop-blur-xl p-4">
                    <div className="w-full max-w-4xl h-full max-h-[90vh] flex flex-col bg-dark-lighter border border-purple-500/20 rounded-[2.5rem] shadow-[0_0_80px_rgba(168,85,247,0.15)] overflow-hidden relative">
                        {/* Floating Close Button */}
                        <button onClick={() => setIsChatModalOpen(false)} className="absolute top-6 left-6 z-10 w-12 h-12 rounded-full bg-dark-lightest/80 flex items-center justify-center text-slate-400 hover:text-white hover:bg-red-500/20 hover:text-red-400 transition-all backdrop-blur-sm">
                            <X size={24} />
                        </button>

                        <div className="flex-1 overflow-y-auto p-6 md:p-10 space-y-8 scroll-smooth pt-20" ref={chatScrollRef}>
                            <div className="text-center mb-8">
                                <div className="w-20 h-20 mx-auto rounded-full bg-primary/20 flex items-center justify-center text-primary border border-primary/20 shadow-[0_0_30px_rgba(168,85,247,0.3)] mb-4">
                                    <Bot size={40} className="animate-pulse" />
                                </div>
                                <h2 className="text-3xl font-bold text-white tracking-tight">Blue</h2>
                                <p className="text-sm text-primary font-medium mt-2">معمار هوشمند آموزش شما</p>
                            </div>

                            {chatMessages.map((msg, idx) => (
                                <div key={idx} className="flex flex-col w-full">
                                    {msg.role === 'user' ? (
                                        <div className="bg-primary/20 text-slate-100 px-8 py-5 rounded-[2rem] rounded-tr-sm max-w-[80%] border border-primary/20 shadow-lg ml-auto text-xl leading-relaxed">
                                            {msg.content}
                                        </div>
                                    ) : (
                                        <div className="text-slate-200 w-full text-lg leading-relaxed py-4 pr-6 border-r-[3px] border-primary/40">
                                            <div dangerouslySetInnerHTML={{ __html: marked.parse(msg.content || '...') }} className={`prose prose-invert prose-purple max-w-none prose-p:text-slate-300 prose-headings:text-white prose-a:text-primary ${isEnglish(msg.content) ? 'ltr-content' : ''}`} />
                                            {idx === chatMessages.length - 1 && pendingCourseData && (
                                                <div className="mt-8">
                                                    <button
                                                        onClick={handleAcceptCourse}
                                                        className="bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700 text-white px-8 py-4 rounded-2xl font-bold flex items-center gap-3 text-lg shadow-[0_0_30px_rgba(16,185,129,0.3)] hover:shadow-[0_0_40px_rgba(16,185,129,0.5)] transition-all transform hover:scale-105"
                                                    >
                                                        <CheckCircle size={24} /> تایید و ساخت دوره
                                                    </button>
                                                </div>
                                            )}
                                        </div>
                                    )}
                                </div>
                            ))}
                            {isChatLoading && (
                                <div className="flex items-center gap-4 pr-6 border-r-[3px] border-primary/40 py-4">
                                    <Loader2 size={28} className="text-primary animate-spin" />
                                    <span className="animate-pulse text-xl text-slate-400">بلو در حال فکر کردن...</span>
                                </div>
                            )}
                        </div>
                        <div className="p-6 md:p-8 bg-gradient-to-t from-dark-lighter via-dark-lighter to-transparent shrink-0">
                            <form onSubmit={(e) => { e.preventDefault(); sendChatMessage(); }} className="flex items-center relative max-w-3xl mx-auto">
                                <input
                                    type="text"
                                    value={chatInput}
                                    onChange={(e) => setChatInput(e.target.value)}
                                    placeholder={pendingCourseData ? "یا تغییرات مورد نظرتان را بنویسید..." : "پاسخ خود را برای بلو بنویسید..."}
                                    className="w-full bg-dark-lightest/80 backdrop-blur-md border border-purple-900/50 rounded-[2rem] py-5 pl-20 pr-8 text-lg text-white focus:outline-none focus:border-primary/80 focus:ring-1 focus:ring-primary/50 transition-all shadow-inner placeholder:text-slate-500"
                                    disabled={isChatLoading}
                                    autoFocus
                                />
                                <button
                                    type="submit"
                                    disabled={isChatLoading || !chatInput.trim()}
                                    className="absolute left-3 top-3 bottom-3 w-14 rounded-[1.5rem] bg-primary/20 hover:bg-primary text-primary hover:text-white transition-all flex items-center justify-center disabled:opacity-0 disabled:scale-90"
                                >
                                    <Send size={24} className="rotate-180" />
                                </button>
                            </form>
                            <p className="text-center text-xs text-slate-500 mt-4 font-mono font-medium">Powered by Blue AI Assistant</p>
                        </div>
                    </div>
                </div>
            )}

            {/* Full Screen Coach Chat Modal */}
            {isCoachFullScreen && isCoachMode && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-dark/95 backdrop-blur-xl p-4">
                    <div className="w-full max-w-4xl h-full max-h-[90vh] flex flex-col bg-dark-lighter border border-purple-500/20 rounded-[2.5rem] shadow-[0_0_80px_rgba(168,85,247,0.15)] overflow-hidden">
                        <div className="p-6 md:p-8 border-b border-purple-900/30 flex justify-between items-center bg-dark-lighter shrink-0">
                            <div className="flex items-center gap-4">
                                <div className="w-12 h-12 rounded-full bg-primary/20 flex items-center justify-center text-primary border border-primary/20 shadow-[0_0_20px_rgba(168,85,247,0.2)]">
                                    <Sparkles size={24} className="animate-pulse" />
                                </div>
                                <div>
                                    <h3 className="text-xl font-bold text-white">دستیار هوشمند درس</h3>
                                    <p className="text-xs text-primary font-medium mt-1">{viewingItem.title}</p>
                                </div>
                            </div>
                            <div className="flex items-center gap-3">
                                <button onClick={() => setIsCoachFullScreen(false)} className="w-12 h-12 rounded-full bg-dark-lightest flex items-center justify-center text-slate-400 hover:text-white hover:bg-primary/20 hover:text-primary transition-all">
                                    <Minimize size={24} />
                                </button>
                                <button onClick={() => { setIsCoachFullScreen(false); setIsCoachMode(false); }} className="w-12 h-12 rounded-full bg-dark-lightest flex items-center justify-center text-slate-400 hover:text-white hover:bg-red-500/20 hover:text-red-400 transition-all">
                                    <X size={24} />
                                </button>
                            </div>
                        </div>
                        <div className="flex-1 overflow-y-auto p-6 md:p-10 space-y-8 scroll-smooth" ref={coachScrollRef}>
                            {coachMessages.map((msg, idx) => (
                                <div key={idx} className="flex flex-col w-full">
                                    {msg.role === 'user' ? (
                                        <div className={`bg-dark-lightest/50 text-slate-100 px-8 py-5 rounded-[2rem] rounded-tr-sm max-w-[80%] border ${vColor.classes.border} shadow-lg ml-auto text-xl leading-relaxed`}>
                                            {msg.content}
                                        </div>
                                    ) : (
                                        <div className={`text-slate-200 w-full text-lg leading-relaxed py-4 pr-6 border-r-[3px] ${vColor.classes.border}`}>
                                            <div dangerouslySetInnerHTML={{ __html: marked.parse(msg.content || '...') }} className={`prose prose-invert max-w-none prose-p:text-slate-300 ${isEnglish(msg.content) ? 'ltr-content' : ''}`} />
                                        </div>
                                    )}
                                </div>
                            ))}
                            {isCoachLoading && (
                                <div className="flex items-center gap-4 pr-6 border-r-[3px] border-primary/40 py-4">
                                    <Loader2 size={28} className="text-primary animate-spin" />
                                    <span className="animate-pulse text-xl text-slate-400">در حال فکر کردن...</span>
                                </div>
                            )}
                        </div>
                        <div className="p-6 md:p-10 bg-dark-lighter border-t border-purple-900/30 shrink-0">
                            <form onSubmit={(e) => { e.preventDefault(); sendCoachMessage(); }} className="flex gap-4 relative max-w-4xl mx-auto">
                                <input
                                    type="text"
                                    value={coachInput}
                                    onChange={(e) => setCoachInput(e.target.value)}
                                    placeholder="سوال خود را بپرسید..."
                                    className="flex-1 bg-dark-lightest border border-purple-900/50 rounded-3xl px-8 py-6 pr-20 text-xl text-white focus:outline-none focus:border-primary focus:ring-2 focus:ring-primary/20 transition-all shadow-2xl shadow-black/50"
                                    disabled={isCoachLoading}
                                />
                                <button
                                    type="submit"
                                    disabled={isCoachLoading || !coachInput.trim()}
                                    className={`absolute right-3 top-3 bottom-3 bg-gradient-to-r ${vColor.classes.from} ${vColor.classes.to} hover:brightness-110 disabled:opacity-50 text-white w-16 rounded-2xl transition-all flex items-center justify-center shadow-xl ${vColor.classes.shadowHover}`}
                                >
                                    <Send size={28} className="rotate-180" />
                                </button>
                            </form>
                        </div>
                    </div>
                </div>
            )}
            {/* Course Settings Modal */}
            {isCourseSettingsModalOpen && editingCourse && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-dark/80 backdrop-blur-md p-4" onClick={() => setIsCourseSettingsModalOpen(false)}>
                    <div className="bg-dark-lighter w-full max-w-xl rounded-[2rem] border border-purple-900/30 overflow-hidden shadow-2xl" onClick={e => e.stopPropagation()}>
                        <div className="p-6 border-b border-purple-900/30 flex justify-between items-center bg-dark-lightest/50">
                            <h3 className="text-xl font-bold text-white flex items-center gap-2"><Settings size={20} className="text-primary" /> تنظیمات دوره</h3>
                            <button onClick={() => setIsCourseSettingsModalOpen(false)} className="text-slate-400 hover:text-white p-2 rounded-full hover:bg-white/5 transition-colors">
                                <X size={20} />
                            </button>
                        </div>
                        <form onSubmit={handleSaveCourseSettings} className="p-6 flex flex-col gap-6">
                            <div>
                                <label className="block text-sm font-medium text-slate-300 mb-2">نام دوره</label>
                                <input
                                    type="text"
                                    value={courseSettingsForm.title}
                                    onChange={(e) => setCourseSettingsForm({...courseSettingsForm, title: e.target.value})}
                                    className="w-full bg-dark-lightest border border-purple-900/50 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-all"
                                    required
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-slate-300 mb-3 flex items-center gap-2"><Palette size={16} /> رنگ اصلی دوره</label>
                                <div className="flex flex-wrap gap-3">
                                    {COURSE_COLORS.map(color => (
                                        <button
                                            key={color.name}
                                            type="button"
                                            onClick={() => setCourseSettingsForm({...courseSettingsForm, color: color.name})}
                                            className={`w-10 h-10 rounded-full flex items-center justify-center transition-all ${courseSettingsForm.color === color.name ? 'ring-2 ring-offset-2 ring-offset-dark-lighter scale-110 shadow-lg' : 'hover:scale-105 opacity-70 hover:opacity-100'} ${color.classes.glow}`}
                                            style={{ backgroundColor: color.hex, '--tw-ring-color': color.hex }}
                                            title={color.label}
                                        >
                                            {courseSettingsForm.color === color.name && <CheckCircle size={20} className="text-white drop-shadow-md" />}
                                        </button>
                                    ))}
                                </div>
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-slate-300 mb-3 flex items-center gap-2"><Image size={16} /> تصویر کاور</label>
                                <div className="flex items-center gap-4">
                                    {courseSettingsForm.preview_image ? (
                                        <div className="w-24 h-24 rounded-xl overflow-hidden relative border border-purple-900/30 group shrink-0">
                                            <img src={courseSettingsForm.preview_image} alt="Preview" className="w-full h-full object-cover" />
                                            <div className="absolute inset-0 bg-dark/60 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center cursor-pointer" onClick={() => coverImageInputRef.current?.click()}>
                                                <Edit2 size={20} className="text-white" />
                                            </div>
                                        </div>
                                    ) : (
                                        <button type="button" onClick={() => coverImageInputRef.current?.click()} className="w-24 h-24 shrink-0 rounded-xl border-2 border-dashed border-purple-900/50 flex flex-col items-center justify-center text-slate-500 hover:text-primary hover:border-primary/50 hover:bg-primary/5 transition-all">
                                            <Plus size={24} />
                                            <span className="text-xs mt-1">انتخاب</span>
                                        </button>
                                    )}
                                    <div className="flex-1">
                                        <input
                                            type="file"
                                            ref={coverImageInputRef}
                                            onChange={(e) => {
                                                if (e.target.files && e.target.files[0]) {
                                                    const file = e.target.files[0];
                                                    setCourseSettingsForm({
                                                        ...courseSettingsForm,
                                                        cover_image: file,
                                                        preview_image: URL.createObjectURL(file)
                                                    });
                                                }
                                            }}
                                            accept="image/*"
                                            className="hidden"
                                        />
                                        <p className="text-xs text-slate-400 mb-2 leading-relaxed">یک تصویر زیبا برای کاور دوره خود انتخاب کنید. (فرمت‌های رایج تصویری)</p>
                                        {courseSettingsForm.preview_image && (
                                            <button type="button" onClick={() => setCourseSettingsForm({...courseSettingsForm, cover_image: null, preview_image: null})} className="text-xs text-red-400 hover:text-red-300 transition-colors">حذف تصویر فعلی</button>
                                        )}
                                    </div>
                                </div>
                            </div>
                            <div className="flex justify-end gap-3 mt-2 pt-6 border-t border-purple-900/30">
                                <button type="button" onClick={() => setIsCourseSettingsModalOpen(false)} className="px-5 py-2.5 rounded-xl text-slate-300 hover:bg-white/5 transition-colors font-medium">انصراف</button>
                                <button type="submit" disabled={loading} className="bg-gradient-to-r from-primary to-indigo-600 hover:brightness-110 text-white px-6 py-2.5 rounded-xl flex items-center gap-2 font-bold shadow-[0_0_20px_rgba(168,85,247,0.3)] transition-all disabled:opacity-50">
                                    {loading ? <Loader2 size={18} className="animate-spin" /> : <CheckCircle size={18} />}
                                    ذخیره تغییرات
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
}

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);