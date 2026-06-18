import React from 'react';

export default function Home() {
  return (
    <main className="min-h-screen relative flex flex-col justify-between overflow-hidden bg-[#020208]">
      {/* Luces de fondo radiales */}
      <div className="absolute top-[-10%] left-[-10%] w-[50%] h-[50%] bg-gradient-radial pointer-events-none" />
      <div className="absolute bottom-[-10%] right-[-10%] w-[50%] h-[50%] bg-gradient-radial pointer-events-none" />

      {/* Header / Navbar */}
      <header className="w-full max-w-7xl mx-auto px-6 py-6 flex justify-between items-center z-10">
        <div className="text-2xl font-extrabold tracking-wider bg-gradient-to-r from-indigo-400 via-purple-400 to-cyan-400 bg-clip-text text-transparent">
          SUPER_PROFESOR
        </div>
        <nav className="hidden md:flex space-x-8 text-sm text-gray-400">
          <a href="#features" className="hover:text-white transition-colors">Características</a>
          <a href="#architecture" className="hover:text-white transition-colors">Arquitectura</a>
          <a href="#next" className="hover:text-white transition-colors">Próximos Pasos</a>
        </nav>
        <a href="/login" className="glass-panel px-5 py-2.5 rounded-full text-sm font-semibold hover:border-indigo-500/50 transition-all inline-block">
          Iniciar Sesión
        </a>
      </header>

      {/* Hero Section */}
      <section className="flex-grow flex flex-col items-center justify-center text-center px-6 relative z-10 py-20 max-w-5xl mx-auto">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-indigo-500/20 bg-indigo-500/5 text-indigo-300 text-xs font-semibold uppercase tracking-widest mb-6">
          <span className="w-2 h-2 rounded-full bg-indigo-400 animate-pulse" />
          Multi-Agent Platform
        </div>
        <h1 className="text-4xl md:text-7xl font-extrabold tracking-tight mb-8 leading-[1.1]">
          Tutoría de Nivel Experto
          <br />
          <span className="bg-gradient-to-r from-indigo-400 via-purple-400 to-cyan-400 bg-clip-text text-transparent">
            Hiperpersonalizada 1:1
          </span>
        </h1>
        <p className="text-lg md:text-xl text-gray-400 max-w-3xl mb-12 leading-relaxed">
          Super_Profesor es un Gemelo Digital docente capaz de estructurar planes de estudio dinámicos, realizar diagnósticos en tiempo real y validar tu código en menos de 90 segundos.
        </p>
        <div className="flex flex-col sm:flex-row gap-4 justify-center w-full max-w-md">
          <button className="bg-gradient-accent text-white px-8 py-4 rounded-xl font-bold hover:opacity-95 transition-opacity shadow-lg shadow-indigo-500/20">
            Comenzar Gratis
          </button>
          <button className="glass-panel text-white px-8 py-4 rounded-xl font-bold hover:border-white/20 transition-all">
            Ver Demo
          </button>
        </div>
      </section>

      {/* Features Grid */}
      <section id="features" className="max-w-7xl mx-auto px-6 py-20 relative z-10 w-full">
        <h2 className="text-3xl md:text-5xl font-bold text-center mb-16">
          Tres Agentes. Un Aprendizaje Sin Fricciones.
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {/* Card Agente Evaluador */}
          <div className="glass-panel-interactive p-8 rounded-2xl flex flex-col justify-between min-h-[300px]">
            <div>
              <div className="w-12 h-12 rounded-xl bg-cyan-500/10 flex items-center justify-center text-cyan-400 font-bold text-2xl mb-6">
                🔍
              </div>
              <h3 className="text-xl font-bold mb-4">Agente Evaluador</h3>
              <p className="text-gray-400 leading-relaxed">
                Realiza diagnósticos rápidos para mapear en tiempo real tus debilidades y vacíos de conocimiento.
              </p>
            </div>
            <div className="text-cyan-400 text-xs font-semibold tracking-wider uppercase mt-6">
              Gemini 3.5 Flash &bull; Latencia Mínima
            </div>
          </div>

          {/* Card Agente Pedagógico */}
          <div className="glass-panel-interactive p-8 rounded-2xl flex flex-col justify-between min-h-[300px]">
            <div>
              <div className="w-12 h-12 rounded-xl bg-indigo-500/10 flex items-center justify-center text-indigo-400 font-bold text-2xl mb-6">
                📚
              </div>
              <h3 className="text-xl font-bold mb-4">Agente Pedagógico</h3>
              <p className="text-gray-400 leading-relaxed">
                Adapta el plan de estudios utilizando analogías personalizadas basadas en tus pasatiempos e intereses.
              </p>
            </div>
            <div className="text-indigo-400 text-xs font-semibold tracking-wider uppercase mt-6">
              Gemini 3.1 Pro &bull; Contexto de 2M tokens
            </div>
          </div>

          {/* Card Agente Validador */}
          <div className="glass-panel-interactive p-8 rounded-2xl flex flex-col justify-between min-h-[300px]">
            <div>
              <div className="w-12 h-12 rounded-xl bg-purple-500/10 flex items-center justify-center text-purple-400 font-bold text-2xl mb-6">
                ✅
              </div>
              <h3 className="text-xl font-bold mb-4">Agente Validador</h3>
              <p className="text-gray-400 leading-relaxed">
                Audita la lógica y sintaxis de tus ejercicios entregados, devolviendo feedback accionable en tiempo récord.
              </p>
            </div>
            <div className="text-purple-400 text-xs font-semibold tracking-wider uppercase mt-6">
              Auditoría en &lt; 90 Segundos
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="w-full max-w-7xl mx-auto px-6 py-8 border-t border-white/5 flex flex-col md:flex-row justify-between items-center z-10 text-gray-500 text-xs">
        <div>&copy; 2026 Super_Profesor. Todos los derechos reservados.</div>
        <div className="flex space-x-6 mt-4 md:mt-0">
          <a href="#" className="hover:text-white transition-colors">Términos de servicio</a>
          <a href="#" className="hover:text-white transition-colors">Privacidad</a>
        </div>
      </footer>
    </main>
  );
}
