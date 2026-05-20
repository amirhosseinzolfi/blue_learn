const { Settings, CheckCircle, User, Zap } = window.Icons;

function SettingsView({ settings, setSettings, onSave, saved }) {
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
                </div>

                {/* Content Area */}
                <div className="flex-1 p-6 md:p-10 flex flex-col relative">
                    <form onSubmit={onSave} className="flex-1 flex flex-col h-full">
                        <div className="flex-1 space-y-8 max-w-4xl">
                            {activeTab === 'profile' && (
                                <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
                                    <div className="mb-8">
                                        <h3 className="text-xl font-bold text-white mb-2">اطلاعات شخصی</h3>
                                        <p className="text-[13px] text-slate-400 leading-relaxed max-w-2xl">این اطلاعات به هوش مصنوعی کمک می‌کند تا با شناخت بهتر شما، دوره‌هایی کاملاً شخصی‌سازی شده و متناسب با نیازهایتان طراحی کند.</p>
                                    </div>
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                        {inputField('name', 'نام کامل', 'text', 'مثال: علی رضایی', '', 'rtl')}
                                        {inputField('age', 'سن', 'number', 'مثال: ۲۵', '', 'rtl')}
                                    </div>
                                    {inputField('education', 'تحصیلات یا حوزه کاری', 'text', 'مثال: دانشجوی مهندسی کامپیوتر', '', 'rtl')}
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                        {textareaField('background_experience', 'تجربیات و مهارت‌ها', 'تخصص‌ها و علاقه‌مندی‌های خود را خلاصه بنویسید...')}
                                        {textareaField('additional_info', 'نکات تکمیلی برای هوش مصنوعی', 'سبک یادگیری مورد علاقه یا اهداف خاص خود را مشخص کنید...')}
                                    </div>
                                </div>
                            )}

                            {activeTab === 'ai' && (
                                <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
                                    <div className="mb-8">
                                        <h3 className="text-xl font-bold text-white mb-2">تنظیمات موتور هوش مصنوعی</h3>
                                        <p className="text-[13px] text-slate-400 leading-relaxed max-w-2xl">کلید دسترسی و مدل پردازشی مورد نظر برای تولید محتوای آموزشی را پیکربندی کنید.</p>
                                    </div>
                                    <div className="space-y-6 max-w-xl">
                                        {inputField('google_api_key', 'کلید دسترسی (Google API Key)', 'password', 'AIzaSy...', '', 'ltr')}
                                        {inputField('model_name', 'مدل پردازشی (Gemini Model)', 'text', 'gemini-flash-latest', '', 'ltr')}
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
