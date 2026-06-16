const { User, Bot, Loader2, Sparkles, CheckCircle } = window.Icons;

function AuthView({ onAuthSuccess }) {
    const [isLogin, setIsLogin] = React.useState(true);
    const [username, setUsername] = React.useState('');
    const [password, setPassword] = React.useState('');
    const [fullName, setFullName] = React.useState('');
    const [age, setAge] = React.useState('');
    const [jobEducation, setJobEducation] = React.useState('');
    const [loading, setLoading] = React.useState(false);
    const [error, setError] = React.useState('');
    const [showPassword, setShowPassword] = React.useState(false);

    // Seed default credentials info message
    React.useEffect(() => {
        setError('');
        if (isLogin) {
            setFullName('');
            setAge('');
            setJobEducation('');
        }
    }, [isLogin]);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        if (!username.trim() || !password) {
            setError('لطفاً نام کاربری و رمز عبور را وارد کنید.');
            return;
        }

        if (!isLogin) {
            if (!fullName.trim()) {
                setError('لطفاً نام و نام خانوادگی خود را وارد کنید.');
                return;
            }
            if (!age.trim()) {
                setError('لطفاً سن خود را وارد کنید.');
                return;
            }
        }

        setLoading(true);
        try {
            let res;
            if (isLogin) {
                res = await api.login(username.trim(), password);
            } else {
                res = await api.register(username.trim(), password, fullName.trim(), age.trim(), jobEducation.trim());
            }
            
            localStorage.setItem('token', res.token);
            localStorage.setItem('username', res.username);
            localStorage.setItem('userId', res.id);
            
            if (onAuthSuccess) {
                onAuthSuccess(res.token, res.username);
            }
        } catch (err) {
            console.error(err);
            const msg = err.response?.data?.detail || 'خطایی رخ داد. لطفاً دوباره تلاش کنید.';
            setError(msg);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen w-full flex items-center justify-center relative overflow-hidden bg-[#07070e] font-sans selection:bg-primary/30 select-none">
            {/* Ambient Background Decorative Glows */}
            <div className="absolute top-[-10%] right-[-10%] w-[50vw] h-[50vw] rounded-full bg-primary/10 blur-[150px] animate-pulse duration-[8000ms] pointer-events-none"></div>
            <div className="absolute bottom-[-10%] left-[-10%] w-[50vw] h-[50vw] rounded-full bg-blue-500/10 blur-[150px] animate-pulse duration-[10000ms] pointer-events-none"></div>

            <div className="w-full max-w-[460px] mx-4 relative z-10 animate-in fade-in zoom-in-95 duration-700">
                
                {/* Glowing Outer Shadow Border Card */}
                <div className="bg-dark-lighter/45 backdrop-blur-3xl border border-white/[0.04] rounded-[2.5rem] p-8 md:p-10 shadow-[0_20px_50px_rgba(0,0,0,0.6)] relative overflow-hidden">
                    
                    {/* Inner glowing edge ornament */}
                    <div className="absolute top-0 inset-x-0 h-[2px] bg-gradient-to-r from-transparent via-primary/50 to-transparent"></div>

                    {/* Logo & Header */}
                    <div className="flex flex-col items-center text-center mb-8">
                        <div className="relative mb-4 flex items-center justify-center w-16 h-16 rounded-[1.25rem] bg-gradient-to-br from-primary to-indigo-600 shadow-[0_8px_32px_rgba(168,85,247,0.3)] animate-bounce duration-[4000ms] overflow-hidden group">
                            <div className="absolute inset-0 bg-white/10 opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
                            <Bot size={32} className="text-white" />
                        </div>
                        <h1 className="text-2xl md:text-3xl font-extrabold text-white tracking-tight mb-2 flex items-center gap-2">
                            <span>بلو لرن</span>
                            <span className="text-primary flex items-center"><Sparkles size={18} className="animate-pulse" /></span>
                        </h1>
                        <p className="text-[12px] md:text-[13px] text-slate-400 font-medium leading-relaxed max-w-[320px]">
                            آموزش هوشمند و شخصی‌سازی شده با قدرت هوش مصنوعی تفسیری
                        </p>
                    </div>

                    {/* Farsi layout error message */}
                    {error && (
                        <div className="bg-rose-500/10 border border-rose-500/20 text-rose-300 text-[13px] rounded-2xl p-4 mb-6 flex items-start gap-3 animate-in slide-in-from-top-2 duration-300">
                            <svg className="w-5 h-5 shrink-0 text-rose-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                                <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                            </svg>
                            <span className="leading-relaxed">{error}</span>
                        </div>
                    )}

                    {/* Form Fields */}
                    <form onSubmit={handleSubmit} className="space-y-5">
                        
                        {/* Username */}
                        <div className="group">
                            <label className="block text-[13px] font-medium text-slate-400 mb-2 group-focus-within:text-primary transition-colors pr-1">
                                نام کاربری
                            </label>
                            <div className="relative">
                                <span className="absolute inset-y-0 right-4 flex items-center text-slate-500 group-focus-within:text-primary transition-colors">
                                    <User size={18} />
                                </span>
                                <input
                                    type="text"
                                    value={username}
                                    onChange={(e) => setUsername(e.target.value)}
                                    placeholder="نام کاربری خود را وارد کنید"
                                    className="w-full bg-dark-lightest/30 hover:bg-dark-lightest/45 border border-white/[0.03] focus:bg-dark-lightest/65 focus:border-primary/40 rounded-2xl pr-12 pl-5 py-3 text-[14px] text-white focus:outline-none focus:ring-4 focus:ring-primary/10 transition-all placeholder:text-slate-600/70"
                                    dir="ltr"
                                    autoComplete="username"
                                />
                            </div>
                        </div>

                        {/* Password */}
                        <div className="group">
                            <label className="block text-[13px] font-medium text-slate-400 mb-2 group-focus-within:text-primary transition-colors pr-1">
                                رمز عبور
                            </label>
                            <div className="relative">
                                <span className="absolute inset-y-0 right-4 flex items-center text-slate-500 group-focus-within:text-primary transition-colors">
                                    {/* Lock SVG */}
                                    <svg className="w-[18px] h-[18px]" fill="none" stroke="currentColor" strokeWidth="2.5" viewBox="0 0 24 24">
                                        <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
                                        <path d="M7 11V7a5 5 0 0 1 10 0v4" />
                                    </svg>
                                </span>
                                <input
                                    type={showPassword ? "text" : "password"}
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    placeholder="رمز عبور خود را وارد کنید"
                                    className="w-full bg-dark-lightest/30 hover:bg-dark-lightest/45 border border-white/[0.03] focus:bg-dark-lightest/65 focus:border-primary/40 rounded-2xl pr-12 pl-12 py-3 text-[14px] text-white focus:outline-none focus:ring-4 focus:ring-primary/10 transition-all placeholder:text-slate-600/70"
                                    dir="ltr"
                                    autoComplete="current-password"
                                />
                                <button
                                    type="button"
                                    onClick={() => setShowPassword(!showPassword)}
                                    className="absolute inset-y-0 left-4 flex items-center text-slate-500 hover:text-slate-300 transition-colors focus:outline-none"
                                >
                                    {showPassword ? (
                                        /* Eye Off */
                                        <svg className="w-[18px] h-[18px]" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                                            <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24" />
                                            <line x1="1" y1="1" x2="23" y2="23" />
                                        </svg>
                                    ) : (
                                        /* Eye */
                                        <svg className="w-[18px] h-[18px]" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                                            <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
                                            <circle cx="12" cy="12" r="3" />
                                        </svg>
                                    )}
                                </button>
                            </div>
                        </div>

                        {!isLogin && (
                            <React.Fragment>
                                {/* Full Name */}
                                <div className="group animate-in slide-in-from-top-2 duration-300">
                                    <label className="block text-[13px] font-medium text-slate-400 mb-2 group-focus-within:text-primary transition-colors pr-1">
                                        نام و نام خانوادگی
                                    </label>
                                    <div className="relative">
                                        <span className="absolute inset-y-0 right-4 flex items-center text-slate-500 group-focus-within:text-primary transition-colors">
                                            <User size={18} />
                                        </span>
                                        <input
                                            type="text"
                                            value={fullName}
                                            onChange={(e) => setFullName(e.target.value)}
                                            placeholder="نام و نام خانوادگی خود را وارد کنید"
                                            className="w-full bg-dark-lightest/30 hover:bg-dark-lightest/45 border border-white/[0.03] focus:bg-dark-lightest/65 focus:border-primary/40 rounded-2xl pr-12 pl-5 py-3 text-[14px] text-white focus:outline-none focus:ring-4 focus:ring-primary/10 transition-all placeholder:text-slate-600/70 text-right"
                                            dir="rtl"
                                        />
                                    </div>
                                </div>

                                {/* Age */}
                                <div className="group animate-in slide-in-from-top-2 duration-300">
                                    <label className="block text-[13px] font-medium text-slate-400 mb-2 group-focus-within:text-primary transition-colors pr-1">
                                        سن
                                    </label>
                                    <div className="relative">
                                        <span className="absolute inset-y-0 right-4 flex items-center text-slate-500 group-focus-within:text-primary transition-colors">
                                            <svg className="w-[18px] h-[18px]" fill="none" stroke="currentColor" strokeWidth="2.5" viewBox="0 0 24 24">
                                                <rect x="3" y="4" width="18" height="18" rx="2" ry="2" />
                                                <line x1="16" y1="2" x2="16" y2="6" />
                                                <line x1="8" y1="2" x2="8" y2="6" />
                                                <line x1="3" y1="10" x2="21" y2="10" />
                                            </svg>
                                        </span>
                                        <input
                                            type="text"
                                            value={age}
                                            onChange={(e) => setAge(e.target.value)}
                                            placeholder="سن خود را وارد کنید (مثال: ۲۴)"
                                            className="w-full bg-dark-lightest/30 hover:bg-dark-lightest/45 border border-white/[0.03] focus:bg-dark-lightest/65 focus:border-primary/40 rounded-2xl pr-12 pl-5 py-3 text-[14px] text-white focus:outline-none focus:ring-4 focus:ring-primary/10 transition-all placeholder:text-slate-600/70 text-right"
                                            dir="rtl"
                                        />
                                    </div>
                                </div>

                                {/* Job or Education */}
                                <div className="group animate-in slide-in-from-top-2 duration-300">
                                    <label className="block text-[13px] font-medium text-slate-400 mb-2 group-focus-within:text-primary transition-colors pr-1 flex items-center justify-between">
                                        <span>شغل یا تحصیلات</span>
                                        <span className="text-[10px] text-slate-500 font-normal">اختیاری</span>
                                    </label>
                                    <div className="relative">
                                        <span className="absolute inset-y-0 right-4 flex items-center text-slate-500 group-focus-within:text-primary transition-colors">
                                            <svg className="w-[18px] h-[18px]" fill="none" stroke="currentColor" strokeWidth="2.5" viewBox="0 0 24 24">
                                                <path d="M22 10v6M2 10l10-5 10 5-10 5z" />
                                                <path d="M6 12v5c0 2 2 3 6 3s6-1 6-3v-5" />
                                            </svg>
                                        </span>
                                        <input
                                            type="text"
                                            value={jobEducation}
                                            onChange={(e) => setJobEducation(e.target.value)}
                                            placeholder="شغل یا رشته تحصیلی خود را وارد کنید"
                                            className="w-full bg-dark-lightest/30 hover:bg-dark-lightest/45 border border-white/[0.03] focus:bg-dark-lightest/65 focus:border-primary/40 rounded-2xl pr-12 pl-5 py-3 text-[14px] text-white focus:outline-none focus:ring-4 focus:ring-primary/10 transition-all placeholder:text-slate-600/70 text-right"
                                            dir="rtl"
                                        />
                                    </div>
                                </div>
                            </React.Fragment>
                        )}

                        {/* Submit Button */}
                        <div className="pt-2">
                            <button
                                type="submit"
                                disabled={loading}
                                className="w-full flex items-center justify-center gap-2 bg-gradient-to-r from-primary to-indigo-600 hover:brightness-110 text-white py-3.5 rounded-2xl text-[14px] font-bold transition-all shadow-[0_4px_20px_rgba(168,85,247,0.25)] hover:shadow-[0_8px_32px_rgba(168,85,247,0.4)] disabled:opacity-50 disabled:pointer-events-none hover:-translate-y-0.5 active:translate-y-0"
                            >
                                {loading ? (
                                    <Loader2 size={16} className="animate-spin" />
                                ) : (
                                    <span>{isLogin ? 'ورود به حساب کاربری' : 'ثبت نام جدید'}</span>
                                )}
                            </button>
                        </div>
                    </form>

                    {/* Auth Toggle Link */}
                    <div className="mt-8 pt-6 border-t border-white/[0.03] text-center">
                        <button
                            type="button"
                            onClick={() => setIsLogin(!isLogin)}
                            className="text-[13px] text-slate-400 hover:text-primary transition-colors font-medium inline-flex items-center gap-1.5 focus:outline-none"
                        >
                            <span>{isLogin ? 'حساب کاربری ندارید؟ ثبت نام کنید' : 'قبلاً ثبت نام کرده‌اید؟ وارد شوید'}</span>
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                                <polyline points="15 18 9 12 15 6" />
                            </svg>
                        </button>
                    </div>

                </div>
            </div>
        </div>
    );
}
