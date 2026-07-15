const { Settings, CheckCircle, User, Zap } = window.Icons;

function SettingsView({ settings, setSettings, onSave, saved, currentUser, onLogout }) {
    const [activeTab, setActiveTab] = React.useState('profile');

    const inputField = (key, label, type = 'text', placeholder = '', hint = '', dir = 'rtl') => (
        <div className="group">
            <label className="block text-[13px] font-medium text-slate-400 mb-2 group-focus-within:text-primary transition-colors">{label}</label>
            <input
                type={type} value={settings[key] || ''} placeholder={placeholder}
                onChange={(e) => setSettings(s => ({ ...s, [key]: e.target.value }))}
                className="w-full bg-dark-lightest/30 hover:bg-dark-lightest/50 border border-white/[0.03] focus:bg-dark-lightest/60 focus:border-primary/40 rounded-2xl px-5 py-3 text-[14px] text-white focus:outline-none focus:ring-4 focus:ring-primary/10 transition-all placeholder:text-slate-600/70"
                dir={dir}
            />
            {hint && <p className="text-[11px] text-slate-500 mt-2 pl-1">{hint}</p>}
        </div>
    );

    const textareaField = (key, label, placeholder = '', hint = '') => (
        <div className="group">
            <label className="block text-[13px] font-medium text-slate-400 mb-2 group-focus-within:text-primary transition-colors">{label}</label>
            <textarea
                value={settings[key] || ''} placeholder={placeholder} rows="3"
                onChange={(e) => setSettings(s => ({ ...s, [key]: e.target.value }))}
                className="w-full bg-dark-lightest/30 hover:bg-dark-lightest/50 border border-white/[0.03] focus:bg-dark-lightest/60 focus:border-primary/40 rounded-2xl px-5 py-4 text-[14px] text-white focus:outline-none focus:ring-4 focus:ring-primary/10 transition-all resize-none placeholder:text-slate-600/70"
                dir="rtl"
            ></textarea>
            {hint && <p className="text-[11px] text-slate-500 mt-2 pl-1">{hint}</p>}
        </div>
    );

    const sectionDivider = (label) => (
        <div className="flex items-center gap-3 my-2">
            <div className="h-px flex-1 bg-white/[0.04]" />
            <span className="text-[10px] font-bold tracking-widest uppercase text-slate-500">{label}</span>
            <div className="h-px flex-1 bg-white/[0.04]" />
        </div>
    );

    return (
        <div className="max-w-5xl mx-auto pb-10">
            <div className="bg-dark-lighter/60 backdrop-blur-2xl border border-white/[0.03] rounded-[2rem] shadow-[0_8px_32px_rgba(0,0,0,0.4)] overflow-hidden flex flex-col md:flex-row min-h-[550px]">
                {/* Tabs Sidebar */}
                <div className="md:w-52 bg-black/10 border-b md:border-b-0 md:border-l border-white/[0.03] p-5 flex flex-col gap-2 shrink-0">
                    <h2 className="text-[10px] font-bold mb-4 mt-2 text-slate-500/80 px-4 tracking-widest uppercase">تنظیمات پلتفرم</h2>
                    <button
                        type="button"
                        onClick={() => setActiveTab('profile')}
                        className={`flex items-center gap-3 px-4 py-3 rounded-2xl transition-all duration-300 text-[13px] font-medium ${activeTab === 'profile' ? 'bg-primary/15 text-primary shadow-[inset_0_1px_0_rgba(255,255,255,0.05)]' : 'text-slate-400 hover:bg-white/[0.03] hover:text-slate-200'}`}
                    >
                        <User size={16} className={activeTab === 'profile' ? "opacity-100" : "opacity-50"} /> پروفایل من
                    </button>
                    <button
                        type="button"
                        onClick={() => setActiveTab('ai')}
                        className={`flex items-center gap-3 px-4 py-3 rounded-2xl transition-all duration-300 text-[13px] font-medium ${activeTab === 'ai' ? 'bg-primary/15 text-primary shadow-[inset_0_1px_0_rgba(255,255,255,0.05)]' : 'text-slate-400 hover:bg-white/[0.03] hover:text-slate-200'}`}
                    >
                        <Zap size={16} className={activeTab === 'ai' ? "opacity-100" : "opacity-50"} /> هوش مصنوعی
                    </button>

                    {onLogout && (
                        <button
                            type="button"
                            onClick={onLogout}
                            className="mt-auto hidden md:flex items-center gap-3 px-4 py-3 rounded-2xl transition-all duration-300 text-[13px] font-medium text-rose-400/90 hover:bg-rose-500/10 hover:text-rose-400 border border-transparent hover:border-rose-500/20"
                        >
                            <svg className="w-[16px] h-[16px]" fill="none" stroke="currentColor" strokeWidth="2.5" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 0 1-3 3H6a3 3 0 0 1-3-3V7a3 3 0 0 1 3-3h4a3 3 0 0 1 3 3v1" />
                            </svg>
                            <span>خروج از حساب</span>
                        </button>
                    )}
                </div>

                {/* Content Area */}
                <div className="flex-1 p-6 md:p-10 flex flex-col relative">
                    <form onSubmit={onSave} className="flex-1 flex flex-col h-full">
                        <div className="flex-1 space-y-8 max-w-4xl">
                            {activeTab === 'profile' && (
                                <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
                                    <div className="mb-8 flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-white/[0.04] pb-6">
                                        <div>
                                            <h3 className="text-xl font-bold text-white mb-1">حساب کاربری و اطلاعات شخصی</h3>
                                            <p className="text-[13px] text-slate-400 leading-relaxed max-w-2xl">نام کاربری فعال شما در سیستم: <span className="text-primary font-extrabold pr-1 select-all">{currentUser}</span></p>
                                        </div>
                                        {onLogout && (
                                            <button
                                                type="button"
                                                onClick={onLogout}
                                                className="shrink-0 flex items-center justify-center gap-2 bg-rose-500/10 hover:bg-rose-500/20 border border-rose-500/20 hover:border-rose-500/40 text-rose-400 px-5 py-2.5 rounded-2xl text-[13px] font-bold transition-all shadow-[0_4px_12px_rgba(244,63,94,0.1)] active:scale-[0.98]"
                                            >
                                                <svg className="w-[16px] h-[16px]" fill="none" stroke="currentColor" strokeWidth="2.5" viewBox="0 0 24 24">
                                                    <path strokeLinecap="round" strokeLinejoin="round" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 0 1-3 3H6a3 3 0 0 1-3-3V7a3 3 0 0 1 3-3h4a3 3 0 0 1 3 3v1" />
                                                </svg>
                                                <span>خروج از حساب</span>
                                            </button>
                                        )}
                                    </div>
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                        {inputField('name', 'نام کامل', 'text', 'مثال: علی رضایی', '', 'rtl')}
                                        {inputField('age', 'سن', 'number', 'مثال: ۲۵', '', 'rtl')}
                                    </div>
                                    {inputField('education', 'تحصیلات یا حوزه کاری', 'text', 'مثال: دانشجوی مهندسی کامپیوتر', '', 'rtl')}
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                        {textareaField('background_experience', 'تجربیات و مهارتها', 'تخصصها و علاقهمندیهای خود را خلاصه بنویسید...')}
                                        {textareaField('additional_info', 'نکات تکمیلی برای هوش مصنوعی', 'سبک یادگیری مورد علاقه یا اهداف خاص خود را مشخص کنید...')}
                                    </div>
                                </div>
                            )}

                            {activeTab === 'ai' && (
                                <div className="space-y-5 animate-in fade-in slide-in-from-bottom-4 duration-500">
                                    <div className="mb-6">
                                        <h3 className="text-xl font-bold text-white mb-2">تنظیمات موتور هوش مصنوعی</h3>
                                        <p className="text-[13px] text-slate-400 leading-relaxed max-w-2xl">تمام تنظیمات زیر فقط برای حساب شما ذخیره میشوند و با سایر کاربران به اشتراک گذاشته نمیشوند.</p>
                                    </div>

                                    <div className="space-y-5 max-w-xl">

                                        {sectionDivider('کلیدهای دسترسی')}

                                        {inputField('google_api_key', 'کلید Gemini API (Google AI)', 'password', 'AIzaSy...', 'برای تمام قابلیتهای متنی هوش مصنوعی استفاده میشود.', 'ltr')}
                                        {inputField('image_api_key', 'کلید API اختصاصی تصویر (اختیاری)', 'password', 'اگر خالی باشد از کلید Gemini API بالا استفاده میشود...', '', 'ltr')}

                                        {sectionDivider('مدلهای متنی')}

                                        {inputField('content_model', 'مدل تولید محتوای دوره', 'text', 'gemini-flash-latest', 'برای نوشتن محتوای جلسات و سرفصلها استفاده میشود.', 'ltr')}
                                        {inputField('coach_model', 'مدل مربی هوشمند', 'text', 'gemini-flash-latest', 'برای دستیار جلسه و مربی طراحی دوره استفاده میشود.', 'ltr')}
                                        {inputField('knowledge_model', 'مدل پایگاه دانش', 'text', 'gemini-flash-lite-latest', 'برای بهروزرسانی پروفایل شناختی و گراف دانش استفاده میشود.', 'ltr')}

                                        {sectionDivider('تولید تصویر')}

                                        {inputField('image_model', 'مدل تولید تصویر', 'text', 'gemini-2.5-flash-image', 'مدل Gemini برای ساخت کاور جلسات و دورهها.', 'ltr')}

                                        <div className="group flex items-start gap-4 mt-2 p-4 rounded-2xl bg-white/[0.02] border border-white/[0.04]">
                                            <input
                                                type="checkbox"
                                                id="auto_generate_covers"
                                                checked={settings.auto_generate_covers || false}
                                                onChange={(e) => setSettings(s => ({ ...s, auto_generate_covers: e.target.checked }))}
                                                className="w-5 h-5 mt-0.5 rounded border-purple-900/50 bg-dark-lightest text-primary focus:ring-primary focus:ring-offset-dark-lighter transition-all"
                                            />
                                            <div>
                                                <label htmlFor="auto_generate_covers" className="block text-[13px] font-bold text-slate-300 mb-1 cursor-pointer select-none">تولید خودکار تصویر کاور جلسات</label>
                                                <p className="text-[11px] text-slate-500 leading-relaxed">با فعالسازی، هنگام تألیف هر جلسه توسط هوش مصنوعی، یک کاور ۱۶:۹ اختصاصی نیز تولید و درج میشود.</p>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            )}
                        </div>

                        <div className="pt-8 mt-auto flex items-center justify-between">
                            <button type="submit" className="flex items-center justify-center gap-2 bg-primary hover:brightness-110 text-white px-8 py-3 rounded-2xl text-[14px] font-bold transition-all shadow-[0_4px_12px_rgba(168,85,247,0.25)] hover:shadow-[0_8px_20px_rgba(168,85,247,0.4)] hover:-translate-y-0.5 active:scale-[0.98]">
                                ذخیره تغییرات
                            </button>
                            {saved && (
                                <span className="text-emerald-400 text-[13px] font-medium flex items-center gap-2 animate-in fade-in slide-in-from-right-4">
                                    <CheckCircle size={16} /> با موفقیت ذخیره شد
                                </span>
                            )}
                        </div>
                    </form>
                </div>
            </div>
        </div>
    );
}
