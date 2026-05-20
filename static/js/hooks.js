// Reusable hooks extracted from the monolithic App component

// Sidebar drag-to-resize
function useSidebarDrag(contentRef) {
    const { useState, useEffect } = React;
    const [sidebarRatio, setSidebarRatio] = useState(33);
    const [isDragging, setIsDragging] = useState(false);

    useEffect(() => {
        const onMove = (e) => {
            if (!isDragging || !contentRef.current) return;
            const rect = contentRef.current.getBoundingClientRect();
            const pct = ((e.clientX - rect.left) / rect.width) * 100;
            if (pct > 20 && pct < 50) setSidebarRatio(pct);
        };
        const onUp = () => setIsDragging(false);
        if (isDragging) {
            document.addEventListener('mousemove', onMove);
            document.addEventListener('mouseup', onUp);
            document.body.style.userSelect = 'none';
        } else {
            document.body.style.userSelect = 'auto';
        }
        return () => {
            document.removeEventListener('mousemove', onMove);
            document.removeEventListener('mouseup', onUp);
        };
    }, [isDragging]);

    return { sidebarRatio, isDragging, startDrag: () => setIsDragging(true) };
}

// Study timer — tracks time while an item is open
function useStudyTimer(viewingItem, currentView, isCoachMode, onTimeSync) {
    const { useState, useEffect, useRef } = React;
    const [studyTimer, setStudyTimer] = useState(0);
    const [isPaused, setIsPaused] = useState(false);
    const studyTimerRef = useRef(0);
    const lastSyncedTimeRef = useRef(0);
    const wasAutoPausedRef = useRef(false);

    // Is the timer allowed to run based on app state?
    const isAppActive = viewingItem && currentView === 'courses' && !isCoachMode;

    // Initial reset when item changes
    useEffect(() => {
        if (!viewingItem) {
            setStudyTimer(0);
            studyTimerRef.current = 0;
            lastSyncedTimeRef.current = 0;
            return;
        }
        const initialTime = viewingItem.study_time || 0;
        setStudyTimer(initialTime);
        studyTimerRef.current = initialTime;
        lastSyncedTimeRef.current = initialTime;
        setIsPaused(false);
        wasAutoPausedRef.current = false;
    }, [viewingItem?.id]);

    // Interval logic
    useEffect(() => {
        if (!isAppActive || isPaused) return;

        const interval = setInterval(() => {
            setStudyTimer(prev => {
                const next = prev + 1;
                studyTimerRef.current = next;
                return next;
            });
        }, 1000);

        return () => clearInterval(interval);
    }, [isAppActive, isPaused, viewingItem?.id]);

    // Robust Sync Logic using fetch + keepalive for reliability
    const performSync = async (itemId, seconds) => {
        if (seconds <= 0 || !itemId) return;
        try {
            // Using native fetch with keepalive to ensure sync works even during page refresh/close
            const response = await fetch(`/items/${itemId}/study-time`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ seconds }),
                keepalive: true
            });
            if (response.ok) {
                const data = await response.json();
                if (onTimeSync && data?.total_study_time) {
                    onTimeSync(itemId, data.total_study_time);
                }
                return data;
            }
        } catch (e) {
            console.error('Sync failed:', e);
        }
    };

    // Handle Page Visibility & View switching
    useEffect(() => {
        const handleVisibility = () => {
            if (document.hidden) {
                if (!isPaused) {
                    setIsPaused(true);
                    wasAutoPausedRef.current = true;
                }
                // Force sync when tab is hidden
                const unsynced = studyTimerRef.current - lastSyncedTimeRef.current;
                if (unsynced > 0 && viewingItem?.id) {
                    performSync(viewingItem.id, unsynced);
                    lastSyncedTimeRef.current = studyTimerRef.current;
                }
            } else {
                if (wasAutoPausedRef.current && isAppActive) {
                    setIsPaused(false);
                    wasAutoPausedRef.current = false;
                }
            }
        };

        document.addEventListener('visibilitychange', handleVisibility);
        return () => document.removeEventListener('visibilitychange', handleVisibility);
    }, [isPaused, isAppActive, viewingItem?.id]);

    // Final Sync on Page Unload (Refresh/Close)
    useEffect(() => {
        const handleUnload = () => {
            const unsynced = studyTimerRef.current - lastSyncedTimeRef.current;
            if (unsynced > 0 && viewingItem?.id) {
                // For unload, we use beacon or keepalive fetch
                const url = `/items/${viewingItem.id}/study-time`;
                const body = JSON.stringify({ seconds: unsynced });
                if (navigator.sendBeacon) {
                    navigator.sendBeacon(url, new Blob([body], { type: 'application/json' }));
                } else {
                    fetch(url, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body, keepalive: true });
                }
            }
        };
        window.addEventListener('beforeunload', handleUnload);
        return () => {
            window.removeEventListener('beforeunload', handleUnload);
            // Also sync when the hook is cleaned up (viewingItem changes)
            handleUnload();
        };
    }, [viewingItem?.id]);

    // Periodic sync (every 20 seconds for better precision)
    useEffect(() => {
        if (!viewingItem || studyTimer === 0 || studyTimer % 20 !== 0) return;
        const unsynced = studyTimer - lastSyncedTimeRef.current;
        if (unsynced > 0) {
            performSync(viewingItem.id, unsynced);
            lastSyncedTimeRef.current = studyTimer;
        }
    }, [studyTimer]);

    const syncNow = async (itemId) => {
        const unsynced = studyTimerRef.current - lastSyncedTimeRef.current;
        if (unsynced > 0) {
            await performSync(itemId || viewingItem?.id, unsynced);
            lastSyncedTimeRef.current = studyTimerRef.current;
        }
    };

    const setManualTime = (newTotalSeconds, itemId) => {
        const id = itemId || viewingItem?.id;
        if (!id) return;
        api.post(`/items/${id}/set-study-time`, { seconds: newTotalSeconds }).then(res => {
            if (onTimeSync && res?.total_study_time) onTimeSync(id, res.total_study_time);
        }).catch(console.error);
        setStudyTimer(newTotalSeconds);
        studyTimerRef.current = newTotalSeconds;
        lastSyncedTimeRef.current = newTotalSeconds;
    };

    return { studyTimer, lastSyncedTimeRef, studyTimerRef, syncNow, isPaused, setIsPaused, setManualTime };
}
