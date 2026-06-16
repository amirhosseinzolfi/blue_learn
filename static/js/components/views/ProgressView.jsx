const {
    BarChart, Clock, CheckCircle, Trophy, Zap, Bot,
    BookOpen, User, Sparkles, RefreshCw, Loader2,
    Play, ChevronLeft, X, MoreVertical, Settings
} = window.Icons;

const Chart = window.ReactApexChart;
const { useState, useEffect, useCallback, useRef } = window.React;

function ConstellationGraph({ nodes, onNodeSelect, selectedNode }) {
    const containerRef = useRef(null);
    const networkRef = useRef(null);
    const dataRef = useRef(null);

    useEffect(() => {
        if (!containerRef.current || !nodes || nodes.length === 0) return;

        // 1. Prepare Nodes and Edges Data
        const visNodes = [];
        const visEdges = [];

        nodes.forEach(n => {
            const masteryPct = Math.round(n.mastery_score * 100);
            
            // Neon glowing colors based on mastery & category
            let nodeColor = {
                background: 'rgba(16, 185, 129, 0.15)', // Emerald/Green for high mastery
                border: '#10b981',
                highlight: { background: 'rgba(16, 185, 129, 0.35)', border: '#34d399' },
                hover: { background: 'rgba(16, 185, 129, 0.25)', border: '#34d399' }
            };

            if (n.mastery_score < 0.3) {
                // Purple for beginners
                nodeColor = {
                    background: 'rgba(168, 85, 247, 0.15)',
                    border: '#a855f7',
                    highlight: { background: 'rgba(168, 85, 247, 0.35)', border: '#c084fc' },
                    hover: { background: 'rgba(168, 85, 247, 0.25)', border: '#c084fc' }
                };
            } else if (n.mastery_score < 0.7) {
                // Blue for intermediates
                nodeColor = {
                    background: 'rgba(59, 130, 246, 0.15)',
                    border: '#3b82f6',
                    highlight: { background: 'rgba(59, 130, 246, 0.35)', border: '#60a5fa' },
                    hover: { background: 'rgba(59, 130, 246, 0.25)', border: '#60a5fa' }
                };
            }

            // Sizing scales with mastery
            const size = 18 + n.mastery_score * 18;

            visNodes.push({
                id: n.concept,
                label: n.concept,
                title: `${n.concept} (${n.category}) - ${masteryPct}% تسلط`,
                value: n.mastery_score,
                size: size,
                color: nodeColor,
                font: {
                    color: '#e2e8f0',
                    face: 'Vazirmatn, Inter, sans-serif',
                    size: 11,
                    bold: { color: '#ffffff', size: 12, face: 'Vazirmatn' }
                },
                shadow: {
                    enabled: true,
                    color: nodeColor.border,
                    size: 12,
                    x: 0,
                    y: 0
                },
                borderWidth: 2,
                borderWidthSelected: 4,
                shape: 'dot'
            });

            // Create connections (prerequisites)
            if (n.prerequisites && Array.isArray(n.prerequisites)) {
                n.prerequisites.forEach(prereq => {
                    const exists = nodes.some(x => x.concept === prereq);
                    if (exists) {
                        visEdges.push({
                            id: `${prereq}-${n.concept}`,
                            from: prereq,
                            to: n.concept,
                            arrows: {
                                to: { enabled: true, scaleFactor: 0.4 }
                            },
                            color: {
                                color: 'rgba(255, 255, 255, 0.08)',
                                highlight: '#10b981',
                                hover: '#34d399'
                            },
                            width: 1.5,
                            selectionWidth: 3.5,
                            smooth: {
                                type: 'curvedCCW',
                                roundness: 0.15
                            }
                        });
                    }
                });
            }
        });

        // Initialize vis datasets
        const visNodesSet = new window.vis.DataSet(visNodes);
        const visEdgesSet = new window.vis.DataSet(visEdges);
        dataRef.current = { nodes: visNodesSet, edges: visEdgesSet };

        const options = {
            nodes: {
                scaling: { min: 12, max: 35 }
            },
            edges: {
                hoverWidth: 2.5
            },
            physics: {
                solver: 'barnesHut',
                barnesHut: {
                    gravitationalConstant: -2800,
                    centralGravity: 0.25,
                    springLength: 140,
                    springConstant: 0.04,
                    damping: 0.095,
                    avoidOverlap: 0.95
                },
                stabilization: {
                    enabled: true,
                    iterations: 100,
                    fit: true
                }
            },
            interaction: {
                hover: true,
                zoomView: true,
                dragView: true,
                dragNodes: true,
                tooltipDelay: 200
            }
        };

        const network = new window.vis.Network(containerRef.current, { nodes: visNodesSet, edges: visEdgesSet }, options);
        networkRef.current = network;

        // Register Node Click selection
        network.on("selectNode", (params) => {
            const nodeId = params.nodes[0];
            const conceptNode = nodes.find(n => n.concept === nodeId);
            if (conceptNode) {
                onNodeSelect(conceptNode);

                // Dynamically highlight direct connecting paths
                const edgeUpdates = visEdges.map(edge => {
                    const isDirect = edge.from === nodeId || edge.to === nodeId;
                    return {
                        id: edge.id,
                        color: {
                            color: isDirect ? '#10b981' : 'rgba(255, 255, 255, 0.02)'
                        },
                        width: isDirect ? 3.5 : 1.0
                    };
                });
                visEdgesSet.update(edgeUpdates);
            }
        });

        network.on("deselectNode", () => {
            onNodeSelect(null);
            // Restore default translucent edges
            const edgeResets = visEdges.map(edge => ({
                id: edge.id,
                color: {
                    color: 'rgba(255, 255, 255, 0.08)'
                },
                width: 1.5
            }));
            visEdgesSet.update(edgeResets);
        });

        return () => {
            if (networkRef.current) {
                networkRef.current.destroy();
                networkRef.current = null;
            }
        };
    }, [nodes]);

    // Handle focus zoom when selectedNode changes externally (e.g. from sidebar clicks)
    useEffect(() => {
        if (!networkRef.current || !selectedNode) return;
        try {
            networkRef.current.selectNodes([selectedNode.concept]);
            networkRef.current.focus(selectedNode.concept, {
                scale: 1.1,
                animation: {
                    duration: 900,
                    easingFunction: "easeInOutQuad"
                }
            });

            // Highlight connections for this programmatically focused node
            if (dataRef.current && dataRef.current.edges) {
                const nodeId = selectedNode.concept;
                const edgeUpdates = [];
                dataRef.current.edges.forEach(edge => {
                    const isDirect = edge.from === nodeId || edge.to === nodeId;
                    edgeUpdates.push({
                        id: edge.id,
                        color: {
                            color: isDirect ? '#10b981' : 'rgba(255, 255, 255, 0.02)'
                        },
                        width: isDirect ? 3.5 : 1.0
                    });
                });
                dataRef.current.edges.update(edgeUpdates);
            }
        } catch (err) {
            console.warn("Could not focus node in Vis.js graph", err);
        }
    }, [selectedNode]);

    return (
        <div className="w-full h-full min-h-[350px] md:min-h-[420px] rounded-[2rem] border border-white/[0.04] bg-[#080811] relative overflow-hidden shadow-2xl">
            {/* Ambient background glow dots for a cosmic stellar feel */}
            <div className="absolute top-1/4 left-1/4 w-64 h-64 bg-indigo-500/[0.06] rounded-full blur-[80px] pointer-events-none" />
            <div className="absolute bottom-1/4 right-1/4 w-64 h-64 bg-emerald-500/[0.05] rounded-full blur-[80px] pointer-events-none" />
            <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,rgba(255,255,255,0.01)_1px,transparent_1px)] bg-[size:24px_24px] pointer-events-none" />
            <div ref={containerRef} className="w-full h-full absolute inset-0 bg-transparent z-10" style={{ direction: 'ltr' }} />
        </div>
    );
}

const ALL_WIDGETS = [
    { id: 'chart', label: 'تحلیل فعالیت روزانه', defaultCol: 'main' },
    { id: 'insights', label: 'تحلیل هوشمند دانش (بینش‌ها)', defaultCol: 'main' },
    { id: 'knowledge_nodes', label: 'نقشه کهکشانی مفاهیم و ارتباطات', defaultCol: 'main' },
    { id: 'learning_style', label: 'سبک یادگیری شخصی', defaultCol: 'main' },
    { id: 'cognitive', label: 'پروفایل شناختی و هوشمند کاربر', defaultCol: 'side' },
    { id: 'strengths', label: 'نقاط قوت و علایق', defaultCol: 'side' },
    { id: 'recommendations', label: 'مسیر یادگیری پیشنهادی', defaultCol: 'side' },
    { id: 'recent', label: 'جلسات اخیر', defaultCol: 'side' },
    { id: 'badges', label: 'نشان‌های افتخار', defaultCol: 'side' }
];

function ProgressView({ stats, insights, isInsightLoading, onGenerateInsight, onSessionClick, visibleSeries, setVisibleSeries, chartPopup, setChartPopup, popupHovered, setPopupHovered, fetchStats, showToast }) {

    const [isMenuOpen, setIsMenuOpen] = useState(false);
    const [isSyncing, setIsSyncing] = useState(false);
    const [selectedNode, setSelectedNode] = useState(null);
    const [nodeSearch, setNodeSearch] = useState('');
    const [isWidgetModalOpen, setIsWidgetModalOpen] = useState(false);
    const [showAllStrengths, setShowAllStrengths] = useState(false);
    const menuRef = useRef(null);

    useEffect(() => {
        const handleClickOutside = (event) => {
            if (menuRef.current && !menuRef.current.contains(event.target)) {
                setIsMenuOpen(false);
            }
        };
        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    const handleRefreshKnowledge = async () => {
        setIsMenuOpen(false);
        setIsSyncing(true);
        if (showToast) showToast('در حال شروع بازسازی کامل پایگاه دانش...', 'info');
        try {
            await api.rebuildProfile();
            if (fetchStats) await fetchStats();
            if (showToast) showToast('پایگاه دانش شما با موفقیت بازسازی و به روز شد!', 'success');
        } catch (e) {
            console.error(e);
            if (showToast) showToast('خطا در بازسازی پایگاه دانش. لطفا دوباره تلاش کنید.', 'error');
        } finally {
            setIsSyncing(false);
        }
    };

    const toggleWidgetVisibility = (widgetId) => {
        setLayout(prev => {
            const isCurrentlyVisible = prev.main.includes(widgetId) || prev.side.includes(widgetId);
            const newLayout = { main: [...prev.main], side: [...prev.side] };
            if (isCurrentlyVisible) {
                // Hide it
                newLayout.main = newLayout.main.filter(id => id !== widgetId);
                newLayout.side = newLayout.side.filter(id => id !== widgetId);
            } else {
                // Show it by adding it to its default column
                const widgetDef = ALL_WIDGETS.find(w => w.id === widgetId);
                const col = widgetDef ? widgetDef.defaultCol : 'side';
                newLayout[col].push(widgetId);
            }
            return newLayout;
        });
    };

    const activityData = stats.activity_data || [];
    const activeDays = activityData.filter(d => d.minutes > 0).length;
    const totalMins = activityData.reduce((s, d) => s + d.minutes, 0);
    const avgMins = activeDays > 0 ? Math.round(totalMins / activeDays) : 0;

    const statCards = [
        { label: 'زمان کل مطالعه', value: formatTime(stats.total_study_time), icon: Clock, classes: 'bg-purple-500/10 border-purple-500/20 text-purple-500', glow: 'bg-purple-500/10' },
        { label: 'جلسات تکمیل شده', value: `${stats.total_completed_sessions} از ${stats.total_sessions}`, icon: CheckCircle, classes: 'bg-emerald-500/10 border-emerald-500/20 text-emerald-500', glow: 'bg-emerald-500/10' },
        { label: 'دوره‌های تمام‌شده', value: `${stats.completed_courses} از ${stats.total_courses}`, icon: Trophy, classes: 'bg-amber-500/10 border-amber-500/20 text-amber-500', glow: 'bg-amber-500/10' },
        { label: 'تسلط کلی', value: `${stats.total_sessions ? Math.round((stats.total_completed_sessions / stats.total_sessions) * 100) : 0}%`, icon: Zap, classes: 'bg-blue-500/10 border-blue-500/20 text-blue-500', glow: 'bg-blue-500/10' },
        { label: 'میانگین مطالعه روزانه', value: avgMins > 0 ? `${avgMins} دقیقه` : '—', icon: BarChart, classes: 'bg-rose-500/10 border-rose-500/20 text-rose-500', glow: 'bg-rose-500/10' },
    ];

    const badges = [
        { id: 'early_bird', icon: Sparkles, label: 'پیشرو',   active: stats.total_completed_sessions >= 1,  color: 'text-purple-500', bg: 'bg-purple-500/10' },
        { id: 'consistent', icon: Clock,    label: 'مداوم',   active: stats.total_study_time >= 3600,         color: 'text-blue-500',   bg: 'bg-blue-500/10' },
        { id: 'expert',    icon: Trophy,   label: 'خبره',    active: stats.completed_courses >= 1,           color: 'text-yellow-500', bg: 'bg-yellow-500/10' },
        { id: 'social',    icon: User,     label: 'فعال',    active: stats.total_sessions >= 10,             color: 'text-emerald-500',bg: 'bg-emerald-500/10' },
        { id: 'fast',      icon: Zap,      label: 'سریع',    active: false,                                  color: 'text-rose-500',   bg: 'bg-rose-500/10' },
        { id: 'scholar',   icon: BookOpen, label: 'دانشور',  active: stats.total_completed_sessions >= 50,   color: 'text-cyan-500',   bg: 'bg-cyan-500/10' },
    ];

    // Responsive design state
    const [isDesktop, setIsDesktop] = useState(window.innerWidth >= 1024);
    useEffect(() => {
        const handleResize = () => setIsDesktop(window.innerWidth >= 1024);
        window.addEventListener('resize', handleResize);
        return () => window.removeEventListener('resize', handleResize);
    }, []);

    // Layout configuration
    const defaultLayout = {
        main: ['chart', 'insights', 'knowledge_nodes', 'learning_style'],
        side: ['cognitive', 'strengths', 'recommendations', 'recent', 'badges']
    };
    const [layout, setLayout] = useState(() => {
        try {
            const savedStr = localStorage.getItem('progressLayoutV4');
            if (savedStr) {
                const saved = JSON.parse(savedStr);
                const allNew = ['knowledge_nodes','user_info','cognitive','strengths','recommendations','learning_style'];
                allNew.forEach(w => {
                    if (!saved.main.includes(w) && !saved.side.includes(w)) {
                        if (['knowledge_nodes','learning_style'].includes(w)) saved.main.push(w);
                        else saved.side.unshift(w);
                    }
                });
                return saved;
            }
        } catch(e) {}
        return defaultLayout;
    });

    useEffect(() => {
        localStorage.setItem('progressLayoutV4', JSON.stringify(layout));
    }, [layout]);

    const [statOrder, setStatOrder] = useState(() => {
        try {
            const saved = localStorage.getItem('progressStatOrderV3');
            if (saved) return JSON.parse(saved);
        } catch(e) {}
        return [0, 1, 2, 3, 4];
    });

    useEffect(() => {
        localStorage.setItem('progressStatOrderV3', JSON.stringify(statOrder));
    }, [statOrder]);

    const [draggedItem, setDraggedItem] = useState(null);

    const handleDropOnCard = (e, targetCol, targetIndex) => {
        e.preventDefault();
        e.stopPropagation();
        if (!draggedItem) return;
        const { id, col: sourceCol, index: sourceIndex } = draggedItem;
        if (sourceCol === targetCol && sourceIndex === targetIndex) return;

        setLayout(prev => {
            const newLayout = { main: [...prev.main], side: [...prev.side] };
            newLayout[sourceCol].splice(sourceIndex, 1);
            newLayout[targetCol].splice(targetIndex, 0, id);
            return newLayout;
        });
        setDraggedItem(null);
    };

    const handleDropOnColumn = (e, targetCol) => {
        e.preventDefault();
        if (!draggedItem) return;
        const { id, col: sourceCol, index: sourceIndex } = draggedItem;
        if (sourceCol === targetCol) {
            setDraggedItem(null);
            return;
        }

        setLayout(prev => {
            const newLayout = { main: [...prev.main], side: [...prev.side] };
            newLayout[sourceCol].splice(sourceIndex, 1);
            newLayout[targetCol].push(id);
            return newLayout;
        });
        setDraggedItem(null);
    };

    const handleStatDrop = (e, targetIndex) => {
        e.preventDefault();
        const sourceIndexStr = e.dataTransfer.getData('statIndex');
        if (!sourceIndexStr) return;
        const sourceIndex = parseInt(sourceIndexStr, 10);
        if (sourceIndex === targetIndex) return;

        setStatOrder(prev => {
            const newOrder = [...prev];
            const [item] = newOrder.splice(sourceIndex, 1);
            newOrder.splice(targetIndex, 0, item);
            return newOrder;
        });
    };

    // Resizer logic
    const [sideWidth, setSideWidth] = useState(() => {
        const saved = localStorage.getItem('progressSideWidth');
        return saved ? parseInt(saved, 10) : 32; // Default 32% for side col
    });
    const containerRef = useRef(null);
    const [isResizing, setIsResizing] = useState(false);

    const handleMouseMove = useCallback((e) => {
        if (!isResizing || !containerRef.current) return;
        const containerRect = containerRef.current.getBoundingClientRect();
        let newSideWidth = ((e.clientX - containerRect.left) / containerRect.width) * 100;
        if (newSideWidth < 20) newSideWidth = 20;
        if (newSideWidth > 50) newSideWidth = 50;
        setSideWidth(Math.round(newSideWidth));
    }, [isResizing]);

    const handleMouseUp = useCallback(() => {
        setIsResizing(false);
    }, []);

    useEffect(() => {
        if (isResizing) {
            window.addEventListener('mousemove', handleMouseMove);
            window.addEventListener('mouseup', handleMouseUp);
            document.body.style.cursor = 'col-resize';
            document.body.style.userSelect = 'none';
        } else {
            window.removeEventListener('mousemove', handleMouseMove);
            window.removeEventListener('mouseup', handleMouseUp);
            document.body.style.cursor = '';
            document.body.style.userSelect = '';
        }
        return () => {
            window.removeEventListener('mousemove', handleMouseMove);
            window.removeEventListener('mouseup', handleMouseUp);
            document.body.style.cursor = '';
            document.body.style.userSelect = '';
        };
    }, [isResizing, handleMouseMove, handleMouseUp]);

    useEffect(() => {
        if (!isResizing) {
            localStorage.setItem('progressSideWidth', sideWidth.toString());
        }
    }, [isResizing, sideWidth]);

    const chartOptions = {
        chart: {
            type: 'area',
            id: 'activity-chart', toolbar: { show: false },
            zoom: { enabled: true, type: 'x', autoScaleYaxis: true },
            fontFamily: 'Vazirmatn, Inter, sans-serif', background: 'transparent',
            events: {
                dataPointMouseEnter: (event, chartContext, config) => {
                    const idx = config.dataPointIndex;
                    if (idx < 0) return;
                    const data = activityData[idx];
                    if (!data) return;
                    const allActive = activityData.filter(d => d.minutes > 0);
                    const allTimeAvg = allActive.length > 0 ? Math.round(allActive.reduce((s, v) => s + v.minutes, 0) / allActive.length) : 0;
                    setChartPopup({ visible: true, data: { ...data, avg_minutes: allTimeAvg }, x: event.clientX, y: event.clientY });
                },
                dataPointMouseLeave: () => {
                    if (!popupHovered) {
                        setChartPopup(p => ({ ...p, visible: false }));
                    }
                }
            }
        },
        xaxis: {
            type: 'datetime',
            min: new Date(Date.now() - 14 * 86400000).getTime(),
            max: new Date().getTime(),
            labels: { style: { colors: '#94a3b8' }, formatter: (val, ts) => ts ? new Date(ts).toLocaleDateString('fa-IR', { month: 'short', day: 'numeric' }) : '' },
            axisBorder: { show: false }, axisTicks: { show: false }, crosshairs: { show: false }, tooltip: { enabled: false }
        },
        yaxis: { labels: { style: { colors: '#94a3b8' } }, crosshairs: { show: true, position: 'back', stroke: { color: '#a855f7', width: 1, dashArray: 4 } } },
        dataLabels: { enabled: false },
        grid: { borderColor: 'rgba(255,255,255,0.05)', strokeDashArray: 4 },
        stroke: { curve: 'smooth', width: [3, 2], dashArray: [0, 8], colors: ['#a855f7', '#fb7185'] },
        fill: { 
            type: 'gradient', 
            gradient: { 
                shadeIntensity: 1, 
                inverseColors: false, 
                opacityFrom: 0.55, 
                opacityTo: 0.05, 
                stops: [0, 90, 100] 
            } 
        },
        colors: ['#a855f7', '#fb7185'],
        markers: { size: [4, 3], colors: ['#a855f7', '#fb7185'], strokeColors: '#1e1e2e', strokeWidth: 2, hover: { size: 6 } },
        theme: { mode: 'dark' }, legend: { show: false }, 
        tooltip: { 
            enabled: true, 
            shared: false, 
            intersect: true, 
            custom: () => '',
            fixed: { enabled: false }
        }
    };

    const chartSeries = [
        { name: 'مطالعه', type: 'area', data: visibleSeries.study ? activityData.map(d => [new Date(d.date).getTime(), d.minutes]) : [] },
        {
            name: 'میانگین کل', type: 'area',
            data: (() => {
                if (!visibleSeries.average) return [];
                let sum = 0, count = 0;
                return activityData.map(d => {
                    if (d.minutes > 0) { sum += d.minutes; count++; }
                    return [new Date(d.date).getTime(), count > 0 ? Math.round(sum / count) : 0];
                });
            })()
        }
    ];

    const renderWidgetContent = (id) => {
        switch (id) {
            case 'chart':
                return (
                    <div className="bg-dark-lighter border border-white/[0.05] rounded-[2rem] p-6 shadow-2xl overflow-hidden h-full min-h-[350px]">
                        <div className="flex items-center justify-between mb-4">
                            <h3 className="text-base font-bold text-white flex items-center gap-2">
                                <BarChart size={18} className="text-primary" /> تحلیل فعالیت روزانه
                            </h3>
                            <div className="flex items-center gap-3">
                                {[
                                    { key: 'study', color: 'bg-primary', shadowColor: 'rgba(168,85,247,0.5)', label: 'مطالعه روزانه' },
                                    { key: 'average', color: 'bg-rose-500', shadowColor: 'rgba(244,63,94,0.5)', label: `میانگین (${avgMins}د)` },
                                ].map(s => (
                                    <button key={s.key} onClick={() => setVisibleSeries(p => ({ ...p, [s.key]: !p[s.key] }))}
                                        className={`flex items-center gap-1.5 transition-all duration-300 ${visibleSeries[s.key] ? 'opacity-100' : 'opacity-30 grayscale'}`}>
                                        <div className={`w-2.5 h-2.5 rounded-full ${s.color} ${visibleSeries[s.key] ? `shadow-[0_0_8px_${s.shadowColor}]` : ''}`} />
                                        <span className="text-[10px] text-slate-400 font-bold hover:text-white transition-colors">{s.label}</span>
                                    </button>
                                ))}
                            </div>
                        </div>
                        <div className="h-[300px] w-full" dir="ltr">
                            <Chart type="area" options={chartOptions} series={chartSeries} height="100%" />
                        </div>
                    </div>
                );
            case 'recent':
                return (
                    <div className="bg-dark-lighter border border-white/[0.05] rounded-[2rem] p-5 shadow-2xl flex flex-col h-full max-h-[500px]">
                        <div className="flex items-center justify-between mb-4">
                            <h3 className="text-base font-bold text-white flex items-center gap-2">
                                <Clock size={16} className="text-slate-400" /> جلسات اخیر
                            </h3>
                            <span className="text-[10px] font-bold text-slate-500 bg-white/5 px-2 py-1 rounded-lg">{stats.recent_completed.length} جلسه</span>
                        </div>
                        <div className="flex-1 overflow-y-auto space-y-1.5 pr-1">
                            {(() => {
                                const seen = new Set();
                                const unique = [...stats.recent_completed].reverse().filter(item => {
                                    if (seen.has(item.id)) return false;
                                    seen.add(item.id); return true;
                                });
                                return unique.length > 0 ? unique.map(item => (
                                    <div key={item.id} onClick={() => onSessionClick({ course_id: item.course_id, item_id: item.id })}
                                        className="flex items-center gap-2.5 p-2.5 rounded-xl border border-transparent hover:border-emerald-500/20 hover:bg-emerald-500/5 cursor-pointer transition-all group">
                                        <div className="w-6 h-6 shrink-0 rounded-lg bg-emerald-500/15 flex items-center justify-center">
                                            <CheckCircle size={12} className="text-emerald-400" />
                                        </div>
                                        <div className="flex-1 min-w-0">
                                            <p className="text-xs font-semibold text-slate-200 truncate group-hover:text-emerald-300 transition-colors">{item.title}</p>
                                            <p className="text-[10px] text-slate-500 truncate">{item.course_title}</p>
                                        </div>
                                        {item.completed_at && (
                                            <span className="text-[9px] text-slate-600 font-mono shrink-0">
                                                {new Date(item.completed_at).toLocaleDateString('fa-IR', { month: 'short', day: 'numeric' })}
                                            </span>
                                        )}
                                    </div>
                                )) : (
                                    <div className="flex flex-col items-center justify-center h-full py-10 text-center">
                                        <Clock size={24} className="text-slate-700 mb-2" />
                                        <p className="text-xs text-slate-500">هنوز جلسه‌ای تکمیل نشده</p>
                                    </div>
                                );
                            })()}
                        </div>
                    </div>
                );
            case 'insights':
                return (
                    <div className="bg-dark-lighter border border-purple-500/20 rounded-[2.5rem] p-8 shadow-2xl relative overflow-hidden h-full">
                        <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-primary via-indigo-500 to-purple-500" />
                        <div className="flex justify-between items-center mb-8">
                            <div>
                                <h3 className="text-xl font-bold text-white flex items-center gap-3">
                                    <Sparkles size={22} className="text-primary animate-pulse" /> تحلیل هوشمند دانش شما
                                </h3>
                                <p className="text-slate-400 text-xs mt-1">بر اساس جلسات و دوره‌هایی که تا کنون گذرانده‌اید</p>
                            </div>
                            <button onClick={onGenerateInsight} disabled={isInsightLoading || stats.total_completed_sessions === 0}
                                className="bg-primary/20 hover:bg-primary text-primary hover:text-white border border-primary/30 px-5 py-2.5 rounded-xl text-sm font-bold transition-all flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed group">
                                {isInsightLoading ? <Loader2 size={18} className="animate-spin" /> : <RefreshCw size={18} className="group-hover:rotate-180 transition-transform duration-500" />}
                                <span className="hidden sm:inline">تحلیل مجدد</span>
                            </button>
                        </div>
                        <div className="space-y-8 max-h-[400px] overflow-y-auto pr-2">
                            {insights.length > 0 ? insights.map((insight, idx) => (
                                <div key={insight.id} className={`relative pb-8 ${idx !== insights.length - 1 ? 'border-b border-white/[0.05]' : ''}`}>
                                    <div className="flex items-center gap-2 text-[10px] text-slate-500 mb-4 font-mono">
                                        <Clock size={12} /> {new Date(insight.created_at).toLocaleDateString('fa-IR')} - {new Date(insight.created_at).toLocaleTimeString('fa-IR')}
                                    </div>
                                    <div className="prose prose-invert prose-sm max-w-none prose-p:text-slate-300 prose-headings:text-white prose-strong:text-primary leading-relaxed"
                                        dangerouslySetInnerHTML={{ __html: marked.parse(insight.content) }} />
                                </div>
                            )) : (
                                <div className="text-center py-20 bg-white/[0.02] rounded-[2rem] border border-dashed border-white/10">
                                    <Bot size={48} className="mx-auto text-slate-600 mb-4 opacity-50" />
                                    <p className="text-slate-400">هنوز هیچ بینشی تولید نشده است. برای دریافت تحلیل هوشمند روی دکمه بالا کلیک کنید.</p>
                                </div>
                            )}
                        </div>
                    </div>
                );
            case 'level':
                return null;
            case 'badges':
                return (
                    <div className="bg-dark-lighter border border-white/[0.05] rounded-[2.5rem] p-8 shadow-2xl h-full">
                        <h3 className="text-xl font-bold text-white mb-6 flex items-center gap-3">
                            <Zap size={22} className="text-yellow-500" /> نشان‌های افتخار
                        </h3>
                        <div className="grid grid-cols-3 gap-4">
                            {badges.map(badge => (
                                <div key={badge.id} className={`flex flex-col items-center gap-2 group ${badge.active ? 'opacity-100' : 'opacity-30 grayscale'}`}>
                                    <div className={`w-14 h-14 rounded-2xl ${badge.bg} border border-white/5 flex items-center justify-center transition-all duration-500 ${badge.active ? 'group-hover:scale-110 group-hover:rotate-12' : ''}`}>
                                        <badge.icon size={28} className={badge.color} />
                                    </div>
                                    <span className="text-[10px] font-bold text-slate-400 text-center">{badge.label}</span>
                                </div>
                            ))}
                        </div>
                    </div>
                );
            case 'cognitive': {
                const cp = stats.cognitive_profile || {};
                const uInfo = stats.user_info || {};
                
                // Progress calculations for integrated level road
                const levelNum = Math.floor((stats.total_study_time || 0) / 3600) + 1;
                const levelProgress = ((stats.total_study_time || 0) % 3600) / 36; // percentage of current hour progress
                const minsToNext = Math.max(0, Math.floor((3600 - ((stats.total_study_time || 0) % 3600)) / 60));
                
                return (
                    <div className="bg-dark-lighter border border-indigo-500/20 rounded-[2.5rem] p-7 shadow-2xl relative overflow-hidden h-full">
                        <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-blue-500 via-indigo-500 to-purple-500" />
                        
                        {/* Combined Header using user's name from user profile card */}
                        <div className="flex items-center gap-4 mb-4">
                            <div className="w-12 h-12 bg-primary/20 rounded-full flex items-center justify-center border border-primary/30 shrink-0">
                                <User size={20} className="text-primary" />
                            </div>
                            <div className="min-w-0 flex-1">
                                <h3 className="text-base font-bold text-white leading-tight truncate">{uInfo.name || 'کاربر مهمان'}</h3>
                                <p className="text-[10px] text-slate-400 mt-0.5">پروفایل هوشمند و وضعیت شناختی</p>
                            </div>
                        </div>

                        {/* Integrated Learning Level Progress Road */}
                        <div className="mb-5 p-3.5 bg-gradient-to-br from-indigo-950/30 to-purple-950/20 border border-indigo-500/10 rounded-2xl relative overflow-hidden">
                            <div className="absolute top-0 right-0 w-20 h-20 bg-primary/5 rounded-full blur-xl pointer-events-none" />
                            <div className="flex items-center justify-between mb-2">
                                <span className="text-xs font-bold text-indigo-300 flex items-center gap-1.5">
                                    <Trophy size={14} className="text-yellow-500" /> سطح {levelNum}
                                </span>
                                <span className="text-[9px] text-indigo-200/60 font-semibold bg-indigo-500/10 px-2 py-0.5 rounded-md border border-indigo-500/20">جوینده مهار‌ت</span>
                            </div>
                            <div className="w-full bg-black/40 h-2 rounded-full overflow-hidden border border-white/5 relative mb-2">
                                <div 
                                    className="bg-gradient-to-r from-primary via-indigo-400 to-purple-400 h-full rounded-full transition-all duration-1000 shadow-[0_0_10px_rgba(168,85,247,0.3)]"
                                    style={{ width: `${levelProgress}%` }}
                                />
                            </div>
                            <div className="flex justify-between items-center text-[9px] text-slate-400">
                                <span>تا سطح بعدی:</span>
                                <span className="font-semibold text-slate-300">{minsToNext} دقیقه مطالعه باقی‌مانده</span>
                            </div>
                        </div>

                        {!stats.cognitive_profile ? (
                            <div className="flex flex-col items-center justify-center py-10 text-center opacity-50">
                                <Bot size={40} className="mb-3 text-indigo-400" />
                                <p className="text-sm text-white font-bold">در حال یادگیری الگوی ذهنی شما...</p>
                                <p className="text-xs text-slate-400 mt-2">به تکمیل دروس ادامه دهید.</p>
                            </div>
                        ) : (
                            <div className="space-y-4">
                                {/* Personality Summary */}
                                {cp.personality_summary && (
                                    <div className="bg-indigo-500/5 border border-indigo-500/15 rounded-2xl p-4">
                                        <p className="text-[10px] text-indigo-400 font-bold mb-2 uppercase tracking-wider">🧠 تحلیل شخصیت یادگیری</p>
                                        <p className="text-[12px] text-slate-300 leading-relaxed">{cp.personality_summary}</p>
                                    </div>
                                )}
                                {/* Key Metrics Row */}
                                <div className="grid grid-cols-3 gap-2">
                                    <div className="bg-white/[0.03] border border-white/[0.05] p-3 rounded-2xl text-center">
                                        <p className="text-[9px] text-slate-500 mb-1">سرعت یادگیری</p>
                                        <p className="text-lg font-black text-indigo-400">x{cp.global_learning_velocity?.toFixed(1) || '1.0'}</p>
                                    </div>
                                    <div className="bg-white/[0.03] border border-white/[0.05] p-3 rounded-2xl text-center">
                                        <p className="text-[9px] text-slate-500 mb-1">ماندگاری</p>
                                        <p className="text-lg font-black text-emerald-400">{((cp.retention_index || 0) * 100).toFixed(0)}%</p>
                                    </div>
                                    <div className="bg-white/[0.03] border border-white/[0.05] p-3 rounded-2xl text-center">
                                        <p className="text-[9px] text-slate-500 mb-1">تمرکز</p>
                                        <p className="text-lg font-black text-blue-400">{cp.attention_span_minutes || 25} دق</p>
                                    </div>
                                </div>
                                {/* Personality Traits */}
                                {cp.cognitive_data?.personality_traits && (
                                    <div className="grid grid-cols-2 gap-2">
                                        {Object.entries(cp.cognitive_data.personality_traits).map(([key, val], i) => (
                                            <div key={i} className="bg-white/[0.02] border border-white/[0.04] p-2.5 rounded-xl">
                                                <p className="text-[9px] text-slate-500 mb-0.5">{{ persistence: 'پشتکار', patience_with_errors: 'صبر در خطا', learning_curiosity: 'کنجکاوی', preferred_session_length: 'طول جلسه' }[key] || key}</p>
                                                <p className="text-xs font-bold text-white">{val}</p>
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>
                        )}
                    </div>
                );
            }
            case 'user_info': {
                return null;
            }
            case 'knowledge_nodes': {
                const nodes = stats.knowledge_nodes || [];
                const filteredNodes = nodes.filter(n => 
                    n.concept.toLowerCase().includes(nodeSearch.toLowerCase()) || 
                    n.category.toLowerCase().includes(nodeSearch.toLowerCase())
                );
                
                return (
                    <div className="bg-dark-lighter border border-emerald-500/10 rounded-[2.5rem] p-8 shadow-2xl relative overflow-hidden h-full flex flex-col min-h-[550px]">
                        <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-emerald-500 via-teal-400 to-emerald-600" />
                        
                        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
                            <div>
                                <h3 className="text-xl font-bold text-white flex items-center gap-3">
                                    <BookOpen size={22} className="text-emerald-400" /> نقشه کهکشانی مفاهیم و ارتباطات دانش
                                </h3>
                                <p className="text-slate-400 text-xs mt-1">
                                    تحلیل گراف ارتباطات، پیش‌نیازها و میزان تسلط شما بر مفاهیم آموزشی استخراج شده توسط هوش مصنوعی
                                </p>
                            </div>
                            
                            {selectedNode && (
                                <button 
                                    onClick={() => setSelectedNode(null)} 
                                    className="bg-white/5 hover:bg-white/10 text-slate-300 hover:text-white px-3 py-1.5 rounded-xl text-xs font-semibold transition-all flex items-center gap-1.5 self-start sm:self-center"
                                >
                                    <X size={14} /> ریست تمرکز گراف
                                </button>
                            )}
                        </div>
                        
                        {nodes.length === 0 ? (
                            <div className="flex flex-col items-center justify-center flex-1 text-center py-20 bg-white/[0.01] rounded-[2rem] border border-dashed border-white/5">
                                <BookOpen size={48} className="mb-4 text-emerald-400/50 animate-pulse" />
                                <p className="text-sm text-white font-bold">هنوز مهارتی استخراج نشده است</p>
                                <p className="text-xs text-slate-500 mt-2 max-w-sm leading-relaxed">
                                    با کامل کردن اولین جلسات و ایجاد دوره‌های جدید، هوش مصنوعی مفاهیم یادگرفته شده و ساختار درختی روابط آن‌ها را در اینجا ترسیم می‌کند.
                                </p>
                            </div>
                        ) : (
                        <div className="flex-1 flex flex-col lg:flex-row gap-6">
                            {/* Constellation Network Graph */}
                            <div className="w-full lg:w-[62%] h-[380px] md:h-[450px] flex flex-col relative group">
                                <ConstellationGraph 
                                    nodes={nodes} 
                                    onNodeSelect={setSelectedNode} 
                                    selectedNode={selectedNode} 
                                />
                                <div className="absolute bottom-4 right-4 bg-black/60 backdrop-blur-md px-3 py-1.5 rounded-xl border border-white/5 text-[9px] text-slate-400 pointer-events-none">
                                    🔍 بزرگ‌نمایی: اسکرول | جابجایی: درگ روی پس‌زمینه
                                </div>
                            </div>
                            
                            {/* Contextual Sidebar Dashboard */}
                            <div className="w-full lg:w-[38%] flex flex-col bg-white/[0.01] border border-white/[0.04] p-5 rounded-[2rem] h-[380px] md:h-[450px] overflow-hidden">
                                {!selectedNode ? (
                                    // Search & Concept List View
                                    <div className="flex flex-col h-full">
                                        <div className="relative mb-4">
                                            <input 
                                                type="text" 
                                                value={nodeSearch}
                                                onChange={(e) => setNodeSearch(e.target.value)}
                                                placeholder="جستجوی مفاهیم و مهارت‌ها..." 
                                                className="w-full bg-white/[0.02] border border-white/10 rounded-xl py-2 px-3 pl-8 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500/50 transition-all font-medium"
                                            />
                                            <div className="absolute left-2.5 top-2.5 text-slate-500">
                                                🔍
                                            </div>
                                        </div>
                                        
                                        <div className="flex-1 overflow-y-auto pr-1 space-y-2 custom-scrollbar">
                                            {filteredNodes.length > 0 ? filteredNodes.map((node, idx) => {
                                                const scorePct = Math.round(node.mastery_score * 100);
                                                let theme = { text: 'text-purple-400', bg: 'bg-purple-500/10', border: 'border-purple-500/20' };
                                                if (node.mastery_score >= 70) theme = { text: 'text-emerald-400', bg: 'bg-emerald-500/10', border: 'border-emerald-500/20' };
                                                else if (node.mastery_score >= 30) theme = { text: 'text-blue-400', bg: 'bg-blue-500/10', border: 'border-blue-500/20' };

                                                return (
                                                    <div 
                                                        key={idx} 
                                                        onClick={() => setSelectedNode(node)}
                                                        className={`p-3 rounded-xl border border-white/[0.03] bg-white/[0.01] hover:bg-white/[0.03] cursor-pointer flex items-center justify-between transition-all duration-300 group hover:scale-[1.01]`}
                                                    >
                                                        <div className="flex flex-col min-w-0 flex-1 pl-3">
                                                            <span className="text-xs font-bold text-slate-200 group-hover:text-white truncate">{node.concept}</span>
                                                            <span className="text-[9px] text-slate-500 mt-0.5 truncate">{node.category}</span>
                                                        </div>
                                                        <div className="flex items-center gap-2">
                                                            <span className={`text-[10px] font-black ${theme.text} ${theme.bg} ${theme.border} border px-2 py-0.5 rounded-lg`}>
                                                                {scorePct}%
                                                            </span>
                                                            <ChevronLeft size={12} className="text-slate-600 group-hover:text-slate-400 transition-colors" />
                                                        </div>
                                                    </div>
                                                );
                                            }) : (
                                                <div className="text-center py-10 opacity-40">
                                                    <p className="text-xs text-slate-400">مهارتی یافت نشد.</p>
                                                </div>
                                            )}
                                        </div>
                                        
                                        <div className="mt-4 pt-3 border-t border-white/[0.04] text-[10px] text-slate-500 leading-relaxed">
                                            💡 <strong>راهنما:</strong> برای مشاهده پیش‌نیازها و رشته‌های اتصالی مفاهیم، روی گره‌های دایره‌ای در نقشه کهکشانی کلیک کنید.
                                        </div>
                                    </div>
                                ) : (
                                    // Selected Concept Detailed Dashboard
                                    <div className="flex flex-col h-full justify-between">
                                        <div className="space-y-5 overflow-y-auto custom-scrollbar pr-1">
                                            {/* Header Pill & Name */}
                                            <div className="flex items-start justify-between gap-3">
                                                <div className="min-w-0">
                                                    <div className="flex items-center gap-2 flex-wrap">
                                                        <span className="text-[9px] font-black tracking-wider uppercase px-2.5 py-1 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                                                            {selectedNode.category}
                                                        </span>
                                                        {(() => {
                                                            const diff = selectedNode.difficulty_level || "مقدماتی";
                                                            let diffClass = "bg-sky-500/10 text-sky-400 border-sky-500/20";
                                                            if (diff === "متوسط") diffClass = "bg-indigo-500/10 text-indigo-400 border-indigo-500/20";
                                                            else if (diff === "پیشرفته") diffClass = "bg-rose-500/10 text-rose-400 border-rose-500/20";
                                                            return (
                                                                <span className={`text-[9px] font-black tracking-wider px-2.5 py-1 rounded-full border ${diffClass}`}>
                                                                    {diff}
                                                                </span>
                                                            );
                                                        })()}
                                                    </div>
                                                    <h4 className="text-lg font-black text-white mt-2 leading-snug drop-shadow-[0_0_8px_rgba(255,255,255,0.1)]">
                                                        {selectedNode.concept}
                                                    </h4>
                                                </div>
                                                <button 
                                                    onClick={() => setSelectedNode(null)}
                                                    className="w-7 h-7 rounded-lg bg-white/5 hover:bg-white/10 flex items-center justify-center text-slate-400 hover:text-white transition-colors"
                                                >
                                                    <X size={14} />
                                                </button>
                                            </div>

                                            {/* Mastery Progress Tracker */}
                                            <div className="bg-white/[0.02] border border-white/[0.03] p-4 rounded-2xl">
                                                <div className="flex justify-between items-center mb-2">
                                                    <span className="text-[10px] text-slate-400 font-bold">سطح تسلط مفهومی</span>
                                                    <span className={`text-xs font-black ${
                                                        selectedNode.mastery_score >= 0.7 
                                                            ? 'text-emerald-400' 
                                                            : selectedNode.mastery_score >= 0.3 
                                                                ? 'text-blue-400' 
                                                                : 'text-purple-400'
                                                    }`}>
                                                        {Math.round(selectedNode.mastery_score * 100)}%
                                                    </span>
                                                </div>
                                                <div className="w-full bg-black/45 h-2 rounded-full overflow-hidden border border-white/5">
                                                    <div 
                                                        className={`h-full rounded-full transition-all duration-700 ${
                                                            selectedNode.mastery_score >= 0.7 
                                                                ? 'bg-gradient-to-r from-emerald-500 to-teal-400 shadow-[0_0_10px_rgba(16,185,129,0.5)]' 
                                                                : selectedNode.mastery_score >= 0.3
                                                                    ? 'bg-gradient-to-r from-blue-500 to-cyan-400 shadow-[0_0_10px_rgba(59,130,246,0.5)]'
                                                                    : 'bg-gradient-to-r from-purple-500 to-indigo-400 shadow-[0_0_10px_rgba(168,85,247,0.5)]'
                                                        }`} 
                                                        style={{ width: `${selectedNode.mastery_score * 100}%` }} 
                                                    />
                                                </div>
                                                
                                                <div className="flex justify-between items-center mt-3 pt-3 border-t border-white/[0.03] text-[9px] text-slate-500 font-mono">
                                                    <span>دقت ارزیابی هوش مصنوعی</span>
                                                    <span className="font-bold text-slate-300">{Math.round(selectedNode.confidence_level * 100)}%</span>
                                                </div>
                                            </div>

                                            {/* Key Terms Section */}
                                            {selectedNode.key_terms && selectedNode.key_terms.length > 0 && (
                                                <div className="space-y-2">
                                                    <span className="text-[10px] text-slate-400 font-bold flex items-center gap-1.5">
                                                        اصطلاحات و مباحث کلیدی
                                                    </span>
                                                    <div className="flex flex-wrap gap-1.5">
                                                        {selectedNode.key_terms.map((term, tIdx) => (
                                                            <span key={tIdx} className="text-[10px] font-semibold bg-white/[0.02] text-slate-300 border border-white/[0.06] px-2.5 py-1 rounded-lg hover:scale-[1.03] hover:bg-white/[0.05] transition-all cursor-default">
                                                                {term}
                                                            </span>
                                                        ))}
                                                    </div>
                                                </div>
                                            )}

                                            {/* Prerequisites Section */}
                                            <div className="space-y-2">
                                                <span className="text-[10px] text-slate-400 font-bold flex items-center gap-1.5">
                                                    🧭 مفاهیم پیش‌نیاز مستقیم
                                                </span>
                                                {selectedNode.prerequisites && selectedNode.prerequisites.length > 0 ? (
                                                    <div className="flex flex-wrap gap-1.5">
                                                        {selectedNode.prerequisites.map((prereq, pIdx) => {
                                                            const prereqNode = nodes.find(n => n.concept === prereq);
                                                            return (
                                                                <button 
                                                                    key={pIdx}
                                                                    onClick={() => prereqNode && setSelectedNode(prereqNode)}
                                                                    className="bg-emerald-500/5 hover:bg-emerald-500/10 text-emerald-300 border border-emerald-500/20 hover:border-emerald-500/40 px-2.5 py-1 rounded-lg text-[10px] font-bold transition-all flex items-center gap-1 active:scale-95"
                                                                    disabled={!prereqNode}
                                                                >
                                                                    <span>{prereq}</span>
                                                                    {prereqNode && <ChevronLeft size={10} />}
                                                                </button>
                                                            );
                                                        })}
                                                    </div>
                                                ) : (
                                                    <p className="text-[11px] text-slate-500 italic font-medium pr-1">
                                                        مفهوم پایه‌ای و بنیادی (بدون پیش‌نیاز ثبت شده)
                                                    </p>
                                                )}
                                            </div>
                                        </div>

                                        {/* Action / Suggestions */}
                                        <div className="mt-4 pt-4 border-t border-white/[0.04]">
                                            <div className="bg-emerald-500/5 rounded-xl p-3 border border-emerald-500/10 text-[10px] text-slate-300 leading-relaxed">
                                                ⚡ <strong>پیشنهاد مربی هوشمند:</strong> 
                                                {selectedNode.mastery_score < 0.5 
                                                    ? ` برای افزایش میزان تسلط بر مفهوم «${selectedNode.concept}»، پیشنهاد می‌شود جلسات آموزشی نیمه‌کاره مرتبط با موضوع را مطالعه و تمرین‌های عملی را تکمیل نمایید.`
                                                    : ` شما تسلط عالی بر «${selectedNode.concept}» دارید! هوش مصنوعی پیشنهاد می‌کند از این مفهوم در پروژه‌های بزرگ‌تر استفاده کرده و مفاهیم پیشرفته پیشنهادی را به عنوان مرز بعدی دنبال کنید.`
                                                }
                                            </div>
                                        </div>
                                    </div>
                                )}
                            </div>
                        </div>
                        )}
                    </div>
                );
            }
            case 'learning_style': {
                const cp2 = stats.cognitive_profile || {};
                const ls = cp2.cognitive_data?.learning_style || {};
                const styleSummary = cp2.learning_style_summary || '';
                const styleItems = [
                    { key: 'hands_on', label: 'عملی / پروژه‌محور', color: 'from-indigo-600 to-indigo-400', icon: '🔧' },
                    { key: 'visual', label: 'بصری / نموداری', color: 'from-blue-600 to-blue-400', icon: '📈' },
                    { key: 'theoretical', label: 'نظری / مفهومی', color: 'from-purple-600 to-purple-400', icon: '📚' },
                    { key: 'self_directed', label: 'مستقل / خودراه', color: 'from-sky-600 to-sky-400', icon: '🎯' },
                ];
                return (
                    <div className="bg-dark-lighter border border-indigo-500/20 rounded-[2.5rem] p-8 shadow-2xl relative overflow-hidden h-full">
                        <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-primary via-indigo-500 to-blue-500" />
                        <h3 className="text-xl font-bold text-white mb-6 flex items-center gap-3">
                            <Sparkles size={22} className="text-primary-light" /> سبک یادگیری شخصی
                        </h3>
                        {!stats.cognitive_profile ? (
                            <div className="flex flex-col items-center justify-center py-10 text-center opacity-50">
                                <Sparkles size={40} className="mb-3 text-primary-light" />
                                <p className="text-sm text-slate-400">پس از تکمیل دروس مشخص می‌شود.</p>
                            </div>
                        ) : (
                        <div className="space-y-5">
                            {styleSummary && (
                                <div className="bg-indigo-500/5 border border-indigo-500/15 rounded-2xl p-4">
                                    <p className="text-[11px] text-indigo-200/80 leading-relaxed">{styleSummary}</p>
                                </div>
                            )}
                            {styleItems.map(({ key, label, color, icon }) => {
                                const val = Math.round((ls[key] || 0) * 100);
                                return (
                                    <div key={key}>
                                        <div className="flex justify-between items-center mb-1.5">
                                            <span className="text-xs text-slate-300 font-medium">{icon} {label}</span>
                                            <span className="text-xs font-black text-white">{val}%</span>
                                        </div>
                                        <div className="w-full bg-black/40 h-2 rounded-full overflow-hidden">
                                            <div className={`bg-gradient-to-r ${color} h-full rounded-full transition-all duration-700`} style={{ width: `${val}%` }} />
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                        )}
                    </div>
                );
            }
            case 'strengths': {
                const cp3 = stats.cognitive_profile || {};
                const strengths = cp3.strength_areas || [];
                const interests = cp3.interests || [];
                
                const visibleStrengths = showAllStrengths ? strengths : strengths.slice(0, 4);
                const visibleInterests = showAllStrengths ? interests : interests.slice(0, 4);

                return (
                    <div className="bg-dark-lighter border border-emerald-500/20 rounded-[2.5rem] p-7 shadow-2xl relative overflow-hidden h-full">
                        <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-emerald-500 via-teal-400 to-emerald-600" />
                        <h3 className="text-lg font-bold text-white mb-5 flex items-center gap-3">
                            <Trophy size={20} className="text-emerald-400" /> نقاط قوت و علایق
                        </h3>
                        <div className="space-y-4">
                            {strengths.length > 0 && (
                                <div>
                                    <p className="text-[10px] text-slate-500 font-bold uppercase tracking-wider mb-3">🏆 حوزه‌های قدرت</p>
                                    <div className="flex flex-wrap gap-2">
                                        {visibleStrengths.map((s, i) => (
                                            <span key={i} className="text-[11px] font-semibold bg-emerald-500/10 text-emerald-300 border border-emerald-500/20 px-3 py-1.5 rounded-xl">{s}</span>
                                        ))}
                                    </div>
                                </div>
                            )}
                            {interests.length > 0 && (
                                <div>
                                    <p className="text-[10px] text-slate-500 font-bold uppercase tracking-wider mb-3">🔍 علایق برجسته</p>
                                    <div className="flex flex-wrap gap-1.5">
                                        {visibleInterests.map((interest, idx) => (
                                            <span key={idx} className="text-[10px] bg-purple-500/10 text-purple-300 border border-purple-500/20 px-2.5 py-1 rounded-lg">{interest}</span>
                                        ))}
                                    </div>
                                </div>
                            )}
                            {strengths.length === 0 && interests.length === 0 && (
                                <div className="flex flex-col items-center justify-center py-8 text-center opacity-50">
                                    <Trophy size={36} className="mb-3 text-emerald-400" />
                                    <p className="text-xs text-slate-400">پس از تکمیل دروس مشخص می‌شود.</p>
                                </div>
                            )}
                            {(strengths.length > 4 || interests.length > 4) && (
                                <div className="pt-2 border-t border-white/[0.03] flex justify-end">
                                    <button 
                                        onClick={() => setShowAllStrengths(prev => !prev)}
                                        className="text-[10px] text-emerald-400 hover:text-emerald-300 font-bold transition-colors flex items-center gap-1 focus:outline-none"
                                    >
                                        <span>{showAllStrengths ? 'مشاهده کمتر' : 'مشاهده همه علایق و نقاط قوت...'}</span>
                                        <span className="text-[8px]">{showAllStrengths ? '▲' : '▼'}</span>
                                    </button>
                                </div>
                            )}
                        </div>
                    </div>
                );
            }
            case 'recommendations': {
                const cp4 = stats.cognitive_profile || {};
                const recs = cp4.recommended_topics || [];
                return (
                    <div className="bg-dark-lighter border border-teal-500/20 rounded-[2.5rem] p-7 shadow-2xl relative overflow-hidden h-full">
                        <h3 className="text-lg font-bold text-white mb-5 flex items-center gap-3">
                            <Sparkles size={20} className="text-teal-400" /> مسیر یادگیری پیشنهادی
                        </h3>
                        {recs.length === 0 ? (
                            <div className="flex flex-col items-center justify-center py-8 text-center opacity-50">
                                <Sparkles size={36} className="mb-3 text-teal-400" />
                                <p className="text-xs text-slate-400">پس از تحلیل مسیر یادگیری شما پیشنهادات نمایش داده می‌شود.</p>
                            </div>
                        ) : (
                        <div className="space-y-2.5">
                            {recs.map((rec, idx) => (
                                <div key={idx} className="flex items-center gap-3 bg-teal-500/5 border border-teal-500/10 p-3 rounded-2xl hover:bg-teal-500/10 transition-colors group">
                                    <div className="w-6 h-6 rounded-full bg-teal-500/20 flex items-center justify-center flex-shrink-0 text-teal-400 text-[10px] font-black">{idx + 1}</div>
                                    <p className="text-[12px] text-slate-200 group-hover:text-teal-300 transition-colors font-medium">{rec}</p>
                                </div>
                            ))}
                        </div>
                        )}
                    </div>
                );
            }
            default:
                return null;
        }
    };

    const renderWidgetWrapper = (id, col, index) => {
        return (
            <div 
                key={id}
                draggable
                onDragStart={e => {
                    setDraggedItem({ id, col, index });
                    e.dataTransfer.setData('text/plain', id);
                    e.dataTransfer.effectAllowed = 'move';
                }}
                onDragOver={e => e.preventDefault()}
                onDrop={e => handleDropOnCard(e, col, index)}
                className={`relative group cursor-grab active:cursor-grabbing transition-transform duration-300 ${draggedItem?.id === id ? 'opacity-40 scale-[0.98]' : 'hover:scale-[1.01]'}`}
            >
                <div className="absolute top-4 left-4 flex items-center gap-1.5 opacity-0 group-hover:opacity-100 transition-opacity z-20">
                    <div className="p-1.5 rounded-lg bg-black/40 text-white hover:bg-black/60 backdrop-blur-md shadow-lg" title="برای جابجایی بکشید">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="9" cy="12" r="1"></circle><circle cx="9" cy="5" r="1"></circle><circle cx="9" cy="19" r="1"></circle><circle cx="15" cy="12" r="1"></circle><circle cx="15" cy="5" r="1"></circle><circle cx="15" cy="19" r="1"></circle></svg>
                    </div>
                    <button 
                        onClick={(e) => { e.preventDefault(); e.stopPropagation(); toggleWidgetVisibility(id); }}
                        className="p-1.5 rounded-lg bg-black/40 text-red-400 hover:text-red-300 hover:bg-black/60 backdrop-blur-md shadow-lg focus:outline-none"
                        title="پنهان کردن ابزارک"
                    >
                        <X size={12} />
                    </button>
                </div>
                {renderWidgetContent(id)}
            </div>
        );
    };

    return (
        <div className="flex flex-col gap-10 animate-in fade-in slide-in-from-bottom-4 duration-700">
            {/* Title row */}
            <div className="flex justify-between items-center">
                <h2 className="text-3xl font-bold flex items-center gap-3 text-white">
                    <BarChart className="text-primary" size={32} /> تابلوی پیشرفت
                </h2>
                <div className="flex items-center gap-3">
                    <div className="bg-dark-lighter border border-white/[0.05] px-4 py-2 rounded-2xl flex items-center gap-2">
                        <Zap className="text-yellow-500" size={18} />
                        <span className="text-sm font-bold text-white">{stats.total_completed_sessions * 10} امتیاز</span>
                    </div>
                    {/* Modern 3-Dot settings menu dropdown */}
                    <div className="relative" ref={menuRef}>
                        <button
                            onClick={() => setIsMenuOpen(!isMenuOpen)}
                            disabled={isSyncing}
                            className={`w-10 h-10 rounded-2xl bg-dark-lighter border border-white/[0.05] flex items-center justify-center text-slate-400 hover:text-white hover:border-white/10 hover:bg-dark-lightest active:scale-95 transition-all shadow-md ${isSyncing ? 'cursor-not-allowed opacity-50' : ''}`}
                            title="تنظیمات پلتفرم دانش"
                        >
                            {isSyncing ? (
                                <Loader2 className="animate-spin text-primary" size={20} />
                            ) : (
                                <MoreVertical size={20} />
                            )}
                        </button>
                        {isMenuOpen && (
                            <div className="absolute left-0 mt-2.5 w-64 bg-[#13131f]/95 backdrop-blur-xl border border-white/[0.08] rounded-3xl shadow-[0_20px_50px_rgba(0,0,0,0.5)] overflow-hidden z-50 animate-in fade-in slide-in-from-top-2 duration-200">
                                <div className="p-1.5 space-y-1">
                                    <button
                                        onClick={handleRefreshKnowledge}
                                        className="w-full flex items-center gap-3 px-4 py-3 rounded-2xl hover:bg-primary/10 border border-transparent hover:border-primary/20 text-right transition-all group"
                                    >
                                        <div className="w-8 h-8 rounded-xl bg-primary/20 flex items-center justify-center group-hover:scale-110 transition-transform">
                                            <RefreshCw size={14} className="text-primary group-hover:rotate-45 transition-transform" />
                                        </div>
                                        <div className="flex-1 text-right">
                                            <p className="text-[12px] font-bold text-slate-200 group-hover:text-primary transition-colors">بروزرسانی هسته دانش</p>
                                            <p className="text-[10px] text-slate-500 font-medium mt-0.5">تحلیل هوش مصنوعی بر اساس تمام دوره‌ها، گفتگوها و فعالیت‌ها</p>
                                        </div>
                                    </button>
                                    
                                    <button
                                        onClick={() => { setIsMenuOpen(false); setIsWidgetModalOpen(true); }}
                                        className="w-full flex items-center gap-3 px-4 py-3 rounded-2xl hover:bg-primary/10 border border-transparent hover:border-primary/20 text-right transition-all group"
                                    >
                                        <div className="w-8 h-8 rounded-xl bg-primary/20 flex items-center justify-center group-hover:scale-110 transition-transform">
                                            <Settings size={14} className="text-primary animate-spin-slow" />
                                        </div>
                                        <div className="flex-1 text-right">
                                            <p className="text-[12px] font-bold text-slate-200 group-hover:text-primary transition-colors">مدیریت ابزارک‌ها</p>
                                            <p className="text-[10px] text-slate-500 font-medium mt-0.5">نمایش یا پنهان‌سازی کارت‌های تابلوی پیشرفت</p>
                                        </div>
                                    </button>
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            </div>

            {/* Stat cards */}
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
                {statOrder.map((statIndex, i) => {
                    const stat = statCards[statIndex];
                    return (
                        <div 
                            key={stat.label}
                            draggable
                            onDragStart={(e) => {
                                e.dataTransfer.setData('statIndex', i.toString());
                                e.dataTransfer.effectAllowed = 'move';
                            }}
                            onDragOver={(e) => e.preventDefault()}
                            onDrop={(e) => handleStatDrop(e, i)}
                            className="bg-dark-lighter border border-white/[0.05] p-5 rounded-3xl shadow-lg relative overflow-hidden group hover:bg-dark-lightest transition-colors cursor-grab active:cursor-grabbing"
                        >
                            <div className="absolute top-2 left-2 opacity-0 group-hover:opacity-100 transition-opacity z-20 text-white/40 hover:text-white bg-black/20 rounded-md p-1" title="برای جابجایی بکشید">
                                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="9" cy="12" r="1"></circle><circle cx="9" cy="5" r="1"></circle><circle cx="9" cy="19" r="1"></circle><circle cx="15" cy="12" r="1"></circle><circle cx="15" cy="5" r="1"></circle><circle cx="15" cy="19" r="1"></circle></svg>
                            </div>
                            <div className={`absolute -right-4 -top-4 w-20 h-20 ${stat.glow} rounded-full blur-2xl group-hover:scale-150 transition-transform duration-700`} />
                            <div className="relative z-10 flex flex-col md:flex-row items-start md:items-center gap-4 pointer-events-none">
                                <div className={`w-12 h-12 shrink-0 rounded-2xl ${stat.classes} border flex items-center justify-center`}>
                                    <stat.icon size={20} />
                                </div>
                                <div>
                                    <p className="text-slate-400 text-xs font-medium mb-1">{stat.label}</p>
                                    <p className="text-lg font-bold text-white tracking-tight">{stat.value}</p>
                                </div>
                            </div>
                        </div>
                    );
                })}
            </div>

            {/* Draggable Layout Columns */}
            <div className="flex flex-col lg:flex-row gap-6 relative min-h-[500px]" ref={containerRef}>
                {/* Main Column */}
                <div 
                    className={`w-full flex flex-col gap-6 transition-all duration-300 ${isResizing ? 'pointer-events-none' : ''}`}
                    style={isDesktop ? { width: `calc(${100 - sideWidth}% - 12px)` } : {}}
                    onDragOver={e => e.preventDefault()}
                    onDrop={e => handleDropOnColumn(e, 'main')}
                >
                    {layout.main.map((id, index) => renderWidgetWrapper(id, 'main', index))}
                    {layout.main.length === 0 && (
                        <div className="border-2 border-dashed border-white/10 rounded-[2rem] flex items-center justify-center h-40 text-slate-500">
                            ابزارک‌ها را اینجا رها کنید
                        </div>
                    )}
                </div>

                {/* Resizer */}
                <div 
                    className="hidden lg:flex w-6 -mx-3 cursor-col-resize group flex-col items-center justify-center relative z-30"
                    onMouseDown={(e) => { e.preventDefault(); setIsResizing(true); }}
                    title="برای تغییر عرض بکشید"
                >
                    <div className={`w-1.5 h-32 rounded-full transition-all duration-300 ${isResizing ? 'bg-primary shadow-[0_0_15px_rgba(168,85,247,0.8)] scale-y-110' : 'bg-white/10 group-hover:bg-primary/50 group-hover:h-40'}`} />
                </div>

                {/* Side Column */}
                <div 
                    className={`w-full flex flex-col gap-6 transition-all duration-300 ${isResizing ? 'pointer-events-none' : ''}`}
                    style={isDesktop ? { width: `calc(${sideWidth}% - 12px)` } : {}}
                    onDragOver={e => e.preventDefault()}
                    onDrop={e => handleDropOnColumn(e, 'side')}
                >
                    {layout.side.map((id, index) => renderWidgetWrapper(id, 'side', index))}
                    {layout.side.length === 0 && (
                        <div className="border-2 border-dashed border-white/10 rounded-[2rem] flex items-center justify-center h-40 text-slate-500">
                            ابزارک‌ها را اینجا رها کنید
                        </div>
                    )}
                </div>
            </div>

            {/* Chart popup */}
            {chartPopup.visible && chartPopup.data && (
                <div id="chart-day-popup"
                    onMouseEnter={() => setPopupHovered(true)}
                    onMouseLeave={() => { setPopupHovered(false); setChartPopup(p => ({ ...p, visible: false })); }}
                    style={{ position: 'fixed', top: Math.min(chartPopup.y - 10, window.innerHeight - 340), left: Math.min(chartPopup.x + 16, window.innerWidth - 280), zIndex: 9999 }}
                    className="w-64 bg-[#13131f]/95 backdrop-blur-xl border border-purple-900/40 rounded-[2rem] shadow-[0_20px_50px_rgba(0,0,0,0.7)] overflow-hidden animate-in fade-in zoom-in-95 duration-200">
                    <div className="px-5 py-4 border-b border-white/[0.06] bg-gradient-to-br from-white/[0.02] to-transparent">
                        <div className="flex items-center justify-between mb-3">
                            <p className="text-[10px] text-slate-500 font-bold uppercase tracking-wider">
                                {new Date(chartPopup.data.date).toLocaleDateString('fa-IR', { weekday: 'long', month: 'long', day: 'numeric' })}
                            </p>
                            <button onClick={() => { setChartPopup(p => ({ ...p, visible: false })); setPopupHovered(false); }}
                                className="w-6 h-6 rounded-full bg-white/5 hover:bg-white/10 flex items-center justify-center text-slate-500 hover:text-white transition-colors">
                                <X size={12} />
                            </button>
                        </div>
                        <div className="space-y-2">
                            <div className="flex items-center justify-between">
                                <span className="text-[11px] text-slate-400">مطالعه واقعی:</span>
                                <span className="text-sm font-black text-white">{chartPopup.data.minutes} دقیقه</span>
                            </div>
                        </div>
                    </div>
                    <div className="p-3 space-y-1">
                        <p className="text-[10px] text-slate-500 font-bold mb-2 px-2 flex items-center gap-1.5">
                            <CheckCircle size={10} className="text-emerald-500" /> جلسات تکمیل شده
                        </p>
                        {chartPopup.data.completed_sessions?.length > 0 ? (
                            chartPopup.data.completed_sessions.map((title, i) => {
                                const matched = stats.recent_completed.find(r => r.title === title);
                                return (
                                    <button key={i}
                                        onClick={() => { setChartPopup(p => ({ ...p, visible: false })); setPopupHovered(false); if (matched) onSessionClick({ course_id: matched.course_id, item_id: matched.id }); }}
                                        disabled={!matched}
                                        className="w-full flex items-center gap-2 px-3 py-2.5 rounded-2xl hover:bg-emerald-500/10 border border-transparent hover:border-emerald-500/20 text-right transition-all group disabled:opacity-40 disabled:cursor-default">
                                        <div className="w-5 h-5 shrink-0 rounded-lg bg-emerald-500/20 flex items-center justify-center group-hover:scale-110 transition-transform">
                                            <Play size={10} className="text-emerald-400" />
                                        </div>
                                        <span className="text-[11px] text-slate-200 group-hover:text-emerald-300 truncate transition-colors flex-1 text-right font-medium">{title}</span>
                                        {matched && <ChevronLeft size={12} className="text-slate-600 group-hover:text-emerald-400 shrink-0 transition-colors" />}
                                    </button>
                                );
                            })
                        ) : (
                            <div className="py-4 text-center">
                                <p className="text-[10px] text-slate-600 italic">جلسه‌ای در این روز تکمیل نشده</p>
                            </div>
                        )}
                    </div>
                </div>
            )}
            {/* Widget management modal */}
            {isWidgetModalOpen && (
                <div className="fixed inset-0 bg-black/85 backdrop-blur-md flex items-center justify-center z-[99999] p-4">
                    <div className="bg-[#12121f] border border-white/10 rounded-[2.5rem] p-6 max-w-md w-full shadow-2xl animate-in zoom-in-95 duration-200">
                        <div className="flex justify-between items-center mb-6">
                            <h3 className="text-lg font-bold text-white flex items-center gap-2">
                                <Settings size={20} className="text-primary" /> مدیریت و شخصی‌سازی ابزارک‌ها
                            </h3>
                            <button 
                                onClick={() => setIsWidgetModalOpen(false)} 
                                className="w-8 h-8 rounded-full bg-white/5 hover:bg-white/10 flex items-center justify-center text-slate-400 hover:text-white transition-colors"
                            >
                                <X size={16} />
                            </button>
                        </div>
                        <div className="space-y-3 max-h-[350px] overflow-y-auto pr-1 custom-scrollbar">
                            {ALL_WIDGETS.map(w => {
                                const isVisible = layout.main.includes(w.id) || layout.side.includes(w.id);
                                return (
                                    <div key={w.id} className="flex items-center justify-between p-3 rounded-2xl bg-white/[0.02] border border-white/[0.04] hover:bg-white/[0.04] transition-colors" dir="rtl">
                                        <span className="text-xs font-semibold text-slate-200">{w.label}</span>
                                        <button 
                                            onClick={() => toggleWidgetVisibility(w.id)}
                                            className={`w-11 h-6 rounded-full transition-all relative focus:outline-none ${isVisible ? 'bg-primary' : 'bg-slate-700'}`}
                                        >
                                            <div className={`w-4 h-4 rounded-full bg-white absolute top-1 transition-all ${isVisible ? 'right-6' : 'right-1'}`} />
                                        </button>
                                    </div>
                                );
                            })}
                        </div>
                        <button 
                            onClick={() => setIsWidgetModalOpen(false)}
                            className="w-full mt-6 bg-primary hover:bg-primary-dark text-white font-bold py-3 rounded-2xl transition-all"
                        >
                            تایید و ذخیره چیدمان
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
}

