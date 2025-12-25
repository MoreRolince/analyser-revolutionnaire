'use client'

import { useEffect, useState, useRef } from 'react'
import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { Logo } from '@/components/logo'

export default function Home() {
  const [isScrolled, setIsScrolled] = useState(false)
  const [scrollY, setScrollY] = useState(0)
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 })
  const [activeStep, setActiveStep] = useState(0)
  const [openFaq, setOpenFaq] = useState<number | null>(null)
  const [activeNavItem, setActiveNavItem] = useState<string>('Solutions')
  const heroRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 50)
      setScrollY(window.scrollY)
    }

    const handleMouseMove = (e: MouseEvent) => {
      setMousePosition({ x: e.clientX, y: e.clientY })
    }

    const observerOptions = {
      threshold: 0.1,
      rootMargin: '0px 0px -50px 0px'
    }

    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add('animate-in-view')
        }
      })
    }, observerOptions)

    const elements = document.querySelectorAll('.scroll-animate')
    elements.forEach((el) => observer.observe(el))

    // Auto-rotate steps
    const stepInterval = setInterval(() => {
      setActiveStep((prev) => (prev + 1) % 4)
    }, 3000)

    window.addEventListener('scroll', handleScroll, { passive: true })
    window.addEventListener('mousemove', handleMouseMove, { passive: true })

    return () => {
      window.removeEventListener('scroll', handleScroll)
      window.removeEventListener('mousemove', handleMouseMove)
      observer.disconnect()
      clearInterval(stepInterval)
    }
  }, [])

  // Observer pour détecter la section active dans la navbar
  useEffect(() => {
    const navObserverOptions = {
      threshold: 0.2,
      rootMargin: '-100px 0px -50% 0px'
    }

    const navObserver = new IntersectionObserver((entries) => {
      // Trier les entrées par leur position dans le viewport
      const visibleSections = entries
        .filter(entry => entry.isIntersecting)
        .sort((a, b) => {
          const aTop = a.boundingClientRect.top
          const bTop = b.boundingClientRect.top
          return aTop - bTop
        })

      if (visibleSections.length > 0) {
        const sectionId = visibleSections[0].target.id
        if (sectionId === 'features') {
          setActiveNavItem('Solutions')
        } else if (sectionId === 'comment-ca-marche') {
          setActiveNavItem('Ressources')
        } else if (sectionId === 'tarifs') {
          setActiveNavItem('Tarifs')
        }
      }
    }, navObserverOptions)

    // Observer les sections de navigation après un court délai pour s'assurer qu'elles sont dans le DOM
    const timeoutId = setTimeout(() => {
      const featuresSection = document.querySelector('#features')
      const commentSection = document.querySelector('#comment-ca-marche')
      const tarifsSection = document.querySelector('#tarifs')

      if (featuresSection) navObserver.observe(featuresSection)
      if (commentSection) navObserver.observe(commentSection)
      if (tarifsSection) navObserver.observe(tarifsSection)
    }, 100)

    return () => {
      navObserver.disconnect()
      clearTimeout(timeoutId)
    }
  }, [])

  const parallaxOffset = scrollY * 0.3

  return (
    <div className="min-h-screen bg-white text-gray-900 overflow-hidden relative">
      {/* Animated Background */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none z-0">
        <div 
          className="absolute inset-0 bg-gradient-to-br from-blue-50/50 via-white to-emerald-50/30 transition-opacity duration-1000"
          style={{ opacity: Math.min(scrollY / 800, 0.4) }}
        />
        <div className="absolute inset-0 opacity-[0.02]" style={{
          backgroundImage: 'linear-gradient(rgba(0,0,0,0.1) 1px, transparent 1px), linear-gradient(90deg, rgba(0,0,0,0.1) 1px, transparent 1px)',
          backgroundSize: '50px 50px'
        }} />
      </div>

      {/* Floating Orbs */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none z-0">
        <div className="absolute top-20 right-20 w-96 h-96 bg-blue-200/20 rounded-full blur-3xl animate-float" />
        <div className="absolute bottom-20 left-20 w-80 h-80 bg-emerald-200/20 rounded-full blur-3xl animate-float" style={{ animationDelay: '2s' }} />
      </div>

      {/* Cursor Glow */}
      <div 
        className="fixed w-[500px] h-[500px] bg-blue-100/30 rounded-full blur-3xl pointer-events-none z-0 transition-all duration-700 ease-out"
        style={{
          left: `${mousePosition.x - 250}px`,
          top: `${mousePosition.y - 250}px`,
          transform: 'translate(-50%, -50%)',
        }}
      />

      {/* Premium Navigation Bar */}
      <header className={`fixed top-0 left-0 right-0 z-50 transition-all duration-500 ${
        isScrolled 
          ? 'bg-white/95 backdrop-blur-xl shadow-lg border-b border-gray-100 py-2 md:py-3' 
          : 'bg-white/80 backdrop-blur-md py-3 md:py-4'
      }`}>
        <nav className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 sm:gap-3">
              <Logo size="sm" />
              <span className="text-lg sm:text-xl font-bold bg-gradient-to-r from-gray-900 to-gray-700 bg-clip-text text-transparent">
                Revenux
              </span>
            </div>
            
            <div className="hidden lg:flex items-center gap-1 bg-gray-100/80 backdrop-blur-sm rounded-full px-2 py-1.5">
              {[
                { label: 'Solutions', href: '#features' },
                { label: 'Ressources', href: '#comment-ca-marche' },
                { label: 'Tarifs', href: '#tarifs' }
              ].map((item) => (
                <button 
                  key={item.label}
                  onClick={() => {
                    const element = document.querySelector(item.href)
                    if (element) {
                      const headerOffset = 80
                      const elementPosition = element.getBoundingClientRect().top
                      const offsetPosition = elementPosition + window.pageYOffset - headerOffset
                      window.scrollTo({
                        top: offsetPosition,
                        behavior: 'smooth'
                      })
                      setActiveNavItem(item.label)
                    }
                  }}
                  className={`px-5 py-2 text-sm font-medium rounded-full transition-all duration-300 ${
                    activeNavItem === item.label
                      ? 'bg-white text-gray-900 shadow-sm'
                      : 'text-gray-600 hover:text-gray-900 hover:bg-white/50'
                  }`}
                >
                  {item.label}
                </button>
              ))}
            </div>

            <div className="flex items-center gap-2 sm:gap-3">
              <Link 
                href="/auth/login" 
                className="hidden sm:block text-sm font-medium text-gray-700 hover:text-gray-900 transition-colors px-3 sm:px-4 py-2 rounded-lg hover:bg-gray-100/50"
              >
                Connexion
              </Link>
              <Link href="/auth/register">
                <Button className="bg-gray-900 text-white hover:bg-gray-800 rounded-full px-4 sm:px-6 py-2 sm:py-2.5 text-xs sm:text-sm font-semibold shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-105">
                  Essai gratuit
                </Button>
              </Link>
            </div>
          </div>
        </nav>
      </header>

      {/* Hero Section */}
      <section 
        ref={heroRef}
        className="relative min-h-screen flex items-center justify-center pt-20 sm:pt-24 pb-16 sm:pb-20 px-4 sm:px-6 z-10"
        style={{
          transform: `translateY(${parallaxOffset}px)`
        }}
      >
        <div className="max-w-7xl mx-auto text-center">
          <div className="mb-6 sm:mb-10 scroll-animate">
            <div className="inline-flex items-center gap-2 sm:gap-3 bg-gradient-to-r from-gray-900 to-gray-800 text-white rounded-full px-4 sm:px-6 py-2 sm:py-3 shadow-2xl hover:shadow-3xl transition-all duration-500 hover:scale-105 group cursor-pointer border border-gray-800">
              <span className="text-xs font-bold uppercase tracking-wider">NEW</span>
              <span className="w-1 h-1 bg-white rounded-full" />
              <span className="text-xs sm:text-sm font-semibold">Trouve des produits digitaux gagnants</span>
              <svg className="w-3 h-3 sm:w-4 sm:h-4 group-hover:translate-x-1 transition-transform duration-300 hidden sm:block" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </div>
          </div>

          <h1 className="text-3xl sm:text-4xl md:text-5xl lg:text-6xl xl:text-7xl font-black mb-6 sm:mb-8 leading-[1.1] tracking-tight scroll-animate px-2">
            <span className="block text-gray-900 animate-fade-in-up" style={{ animationDelay: '0.1s' }}>
              Trouve les produits digitaux
            </span>
            <span className="block bg-gradient-to-r from-gray-900 via-gray-800 to-gray-900 bg-clip-text text-transparent mt-2 animate-fade-in-up" style={{ animationDelay: '0.2s' }}>
              qui génèrent du revenu
            </span>
          </h1>

          <p className="text-base sm:text-lg md:text-xl text-gray-600 mb-8 sm:mb-12 max-w-3xl mx-auto leading-relaxed font-normal scroll-animate animate-fade-in-up px-4" style={{ animationDelay: '0.4s' }}>
            Analyse des milliers de produits digitaux sur les marketplaces africaines. Découvre ceux qui cartonnent avec des données réelles et vérifiées.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-3 sm:gap-4 mb-12 sm:mb-16 scroll-animate animate-scale-in px-4" style={{ animationDelay: '0.5s' }}>
            <Link href="/auth/register" className="group w-full sm:w-auto">
              <Button className="w-full sm:w-auto bg-gray-900 text-white hover:bg-gray-800 rounded-full px-6 sm:px-10 py-4 sm:py-6 text-base sm:text-lg font-semibold shadow-2xl hover:shadow-3xl transition-all duration-300 hover:scale-105">
                <span className="flex items-center justify-center gap-2">
                  Découvrir les produits gagnants
                  <svg className="w-4 h-4 sm:w-5 sm:h-5 group-hover:translate-x-1 transition-transform duration-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                  </svg>
                </span>
              </Button>
            </Link>
            <Link href="/dashboard" className="group w-full sm:w-auto">
              <Button className="w-full sm:w-auto bg-white border-2 border-gray-300 text-gray-900 hover:border-gray-400 hover:bg-gray-50 rounded-full px-6 sm:px-10 py-4 sm:py-6 text-base sm:text-lg font-semibold shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-105">
                Voir les plans
                <svg className="w-4 h-4 sm:w-5 sm:h-5 ml-2 group-hover:translate-x-1 transition-transform duration-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
              </Button>
            </Link>
          </div>

          <div className="flex items-center justify-center gap-2 sm:gap-4 scroll-animate animate-fade-in-up px-4" style={{ animationDelay: '0.6s' }}>
            <div className="flex items-center gap-2">
              <div className="flex -space-x-2">
                {[1,2,3,4].map((i) => (
                  <div key={i} className="w-6 h-6 sm:w-8 sm:h-8 rounded-full bg-gradient-to-br from-blue-500 to-blue-600 border-2 border-white shadow-sm" />
                ))}
              </div>
              <span className="text-xs sm:text-sm font-semibold text-gray-700 ml-1 sm:ml-2">
                +29,870 e-commerçants
              </span>
            </div>
          </div>
        </div>

        <div className="absolute bottom-8 sm:bottom-12 left-1/2 -translate-x-1/2 animate-bounce">
          <div className="w-5 h-8 sm:w-6 sm:h-10 border-2 border-gray-400 rounded-full flex items-start justify-center p-1.5 sm:p-2">
            <div className="w-1 h-1 sm:w-1.5 sm:h-1.5 bg-gray-400 rounded-full" />
          </div>
        </div>
      </section>

      {/* How It Works Section */}
      <section id="comment-ca-marche" className="relative py-20 md:py-32 px-4 sm:px-6 z-10 bg-gradient-to-b from-white to-gray-50">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-12 md:mb-20 scroll-animate">
            <h2 className="text-3xl sm:text-4xl md:text-5xl font-black mb-4 text-gray-900 tracking-tight">
              Comment ça marche
            </h2>
            <p className="text-sm sm:text-base md:text-lg text-gray-600 max-w-2xl mx-auto font-normal px-4">
              En 3 étapes simples, trouve et lance tes produits digitaux gagnants
            </p>
          </div>

          <div className="flex flex-col md:flex-row items-center justify-center gap-4 md:gap-6 lg:gap-8 max-w-5xl mx-auto px-4">
            {[
              { number: '01', title: 'Découvre', desc: 'Parcours notre base de produits digitaux gagnants filtrés par niche, prix et croissance', icon: '🔍' },
              { number: '02', title: 'Analyse', desc: 'Ouvre la fiche détaillée avec images réelles, description, prix et liens vérifiés', icon: '📊' },
              { number: '03', title: 'Lance', desc: 'Exporte et teste rapidement ton produit digital, déjà prêt à être vendu', icon: '🚀' },
            ].map((step, idx) => (
              <div key={idx} className="relative w-full md:w-auto scroll-animate" style={{ animationDelay: `${idx * 0.2}s` }}>
                <div className={`bg-gradient-to-br from-gray-50 to-white rounded-xl md:rounded-2xl lg:rounded-3xl p-5 sm:p-6 md:p-10 shadow-lg hover:shadow-2xl transition-all duration-500 hover:scale-105 border-2 ${
                  activeStep === idx ? 'border-gray-900' : 'border-gray-100'
                }`}>
                  <div className="text-4xl sm:text-5xl md:text-6xl font-black text-gray-200 mb-3 md:mb-4">{step.number}</div>
                  <h3 className="text-base sm:text-lg md:text-xl font-bold text-gray-900 mb-2 md:mb-3">{step.title}</h3>
                  <p className="text-xs sm:text-sm md:text-base text-gray-600 leading-relaxed">{step.desc}</p>
                </div>
                {idx < 2 && (
                  <div className="hidden md:block absolute top-1/2 -right-4 w-8 h-0.5 bg-gray-300 z-10">
                    <div className="absolute right-0 top-1/2 -translate-y-1/2 w-0 h-0 border-l-8 border-l-gray-300 border-t-4 border-t-transparent border-b-4 border-b-transparent" />
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="relative py-20 md:py-32 px-4 sm:px-6 z-10 bg-white">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-12 md:mb-20 scroll-animate">
            <h2 className="text-3xl sm:text-4xl md:text-5xl font-black mb-4 text-gray-900 tracking-tight">
              Tout ce dont tu as besoin
              <br />
              <span className="text-gray-600">pour réussir</span>
            </h2>
            <p className="text-sm sm:text-base md:text-lg text-gray-600 max-w-2xl mx-auto font-normal px-4">
              Une plateforme complète pour trouver, analyser et lancer tes produits digitaux gagnants
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-6 md:gap-8 lg:gap-12">
            {[
              {
                title: 'Produits Gagnants',
                description: 'Découvre les produits digitaux qui génèrent le plus de revenus grâce à notre intelligence artificielle qui analyse les tendances du marché en temps réel.',
                icon: (
                  <svg className="w-10 h-10" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                ),
                delay: '0.1s'
              },
              {
                title: 'Analyse Avancée',
                description: 'Analyse complète des performances, du trafic, des publicités actives et des tendances du marché pour chaque produit.',
                icon: (
                  <svg className="w-10 h-10" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                  </svg>
                ),
                delay: '0.2s'
              },
              {
                title: 'Lancement Rapide',
                description: 'Lance tes produits digitaux rapidement avec toutes les données nécessaires prêtes à l\'emploi.',
                icon: (
                  <svg className="w-10 h-10" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                ),
                delay: '0.3s'
              }
            ].map((feature, idx) => (
              <div
                key={idx}
                className="group bg-gradient-to-br from-gray-50 to-white rounded-2xl md:rounded-3xl p-6 md:p-10 shadow-sm hover:shadow-2xl transition-all duration-500 hover:scale-105 hover:-translate-y-2 border border-gray-100 scroll-animate"
                style={{ animationDelay: feature.delay }}
              >
                <div className="w-12 h-12 sm:w-14 sm:h-14 md:w-16 md:h-16 rounded-xl md:rounded-2xl bg-gray-900 flex items-center justify-center text-white mb-4 md:mb-6 group-hover:scale-110 group-hover:rotate-3 transition-all duration-500 shadow-lg">
                  {feature.icon}
                </div>
                <h3 className="text-lg sm:text-xl font-bold text-gray-900 mb-2 md:mb-3">{feature.title}</h3>
                <p className="text-sm sm:text-base text-gray-600 leading-relaxed">{feature.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Comparison Section */}
      <section className="relative py-20 md:py-32 px-4 sm:px-6 z-10 bg-gray-50">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-12 md:mb-20 scroll-animate">
            <h2 className="text-3xl sm:text-4xl md:text-5xl font-black mb-4 text-gray-900 tracking-tight">
              Pourquoi choisir Revenux ?
            </h2>
          </div>

          <div className="grid md:grid-cols-2 gap-4 md:gap-6 lg:gap-8">
            <div className="bg-white rounded-xl md:rounded-2xl lg:rounded-3xl p-5 sm:p-6 md:p-10 shadow-lg border border-gray-200 scroll-animate">
              <div className="flex items-center gap-2 sm:gap-3 md:gap-4 mb-4 md:mb-5 lg:mb-6">
                <div className="w-8 h-8 sm:w-10 sm:h-10 md:w-12 md:h-12 rounded-lg md:rounded-xl bg-green-100 flex items-center justify-center flex-shrink-0">
                  <svg className="w-4 h-4 sm:w-5 sm:h-5 md:w-6 md:h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                </div>
                <h3 className="text-base sm:text-lg md:text-xl font-bold text-gray-900">Avec Revenux</h3>
              </div>
              <ul className="space-y-2 sm:space-y-3 md:space-y-4">
                {['Gagne du temps avec des données prêtes à l\'emploi', 'Découvre les tendances avant tes concurrents', 'Accède à des milliers de produits vérifiés', 'Analyse intelligente des opportunités', 'Lance tes produits en quelques clics'].map((item, idx) => (
                  <li key={idx} className="flex items-start gap-2 sm:gap-3 text-gray-700">
                    <svg className="w-4 h-4 sm:w-5 sm:h-5 text-green-600 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                    <span className="text-xs sm:text-sm md:text-base leading-relaxed">{item}</span>
                  </li>
                ))}
              </ul>
            </div>

            <div className="bg-white rounded-xl md:rounded-2xl lg:rounded-3xl p-5 sm:p-6 md:p-10 shadow-lg border border-gray-200 scroll-animate" style={{ animationDelay: '0.2s' }}>
              <div className="flex items-center gap-2 sm:gap-3 md:gap-4 mb-4 md:mb-5 lg:mb-6">
                <div className="w-8 h-8 sm:w-10 sm:h-10 md:w-12 md:h-12 rounded-lg md:rounded-xl bg-red-100 flex items-center justify-center flex-shrink-0">
                  <svg className="w-4 h-4 sm:w-5 sm:h-5 md:w-6 md:h-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </div>
                <h3 className="text-base sm:text-lg md:text-xl font-bold text-gray-900">Sans Revenux</h3>
              </div>
              <ul className="space-y-2 sm:space-y-3 md:space-y-4">
                {['Perds des heures à chercher manuellement', 'Rate les opportunités qui passent', 'Utilise des données obsolètes', 'Pas d\'analyse des tendances', 'Difficulté à identifier les produits gagnants'].map((item, idx) => (
                  <li key={idx} className="flex items-start gap-2 sm:gap-3 text-gray-700">
                    <svg className="w-4 h-4 sm:w-5 sm:h-5 text-red-600 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                    <span className="text-xs sm:text-sm md:text-base leading-relaxed">{item}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="relative py-16 md:py-24 px-4 sm:px-6 bg-gray-900 z-10 scroll-animate">
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6 md:gap-12 text-center">
            {[
              { number: '29,870+', label: 'E-commerçants actifs' },
              { number: '1M+', label: 'Produits analysés' },
              { number: '50K+', label: 'Boutiques trackées' },
              { number: '98%', label: 'Taux de satisfaction' }
            ].map((stat, idx) => (
              <div key={idx} className="text-white scroll-animate" style={{ animationDelay: `${idx * 0.1}s` }}>
                <div className="text-3xl sm:text-4xl md:text-5xl lg:text-6xl xl:text-7xl font-black mb-2 md:mb-3 bg-gradient-to-r from-white to-gray-300 bg-clip-text text-transparent">
                  {stat.number}
                </div>
                <div className="text-gray-400 text-xs sm:text-sm md:text-base lg:text-lg font-medium px-2">{stat.label}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Testimonials Section */}
      <section className="relative py-20 md:py-32 px-4 sm:px-6 z-10 bg-white">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-12 md:mb-20 scroll-animate">
            <h2 className="text-3xl sm:text-4xl md:text-5xl font-black mb-4 text-gray-900 tracking-tight">
              Ils nous font
              <br />
              <span className="text-gray-600">confiance</span>
            </h2>
          </div>

          <div className="grid md:grid-cols-3 gap-6 md:gap-8">
            {[
              {
                stars: 5,
                text: "J'AI TROUVÉ MON PRODUIT GAGNANT SUR REVENUX ET GÉNÉRER 32K€ EN 2 MOIS.",
                author: "Richard S.",
                days: "6 jours"
              },
              {
                stars: 5,
                text: "C'EST FACILE, ET ACCESSIBLE MÊME AUX DÉBUTANTS. J'AI TROUVÉ MON PRODUIT GAGNANT EN QUELQUES MINUTES",
                author: "Mickey J.",
                days: "3 jours"
              },
              {
                stars: 5,
                text: "C'EST LE SEUL OUTIL DONT J'AI EU BESOIN POUR COMMENCER L'ECOM. IL Y A TOUT CE QU'IL FAUT.",
                author: "Sara P.",
                days: "12 jours"
              }
            ].map((testimonial, idx) => (
              <div
                key={idx}
                className="group bg-gradient-to-br from-gray-50 to-white rounded-2xl md:rounded-3xl p-6 md:p-10 shadow-sm hover:shadow-2xl transition-all duration-500 hover:scale-105 border border-gray-100 scroll-animate"
                style={{ animationDelay: `${idx * 0.15}s` }}
              >
                <div className="flex justify-center mb-4 md:mb-6">
                  {Array.from({ length: testimonial.stars }).map((_, i) => (
                    <svg key={i} className="w-5 h-5 sm:w-6 sm:h-6 text-yellow-400" fill="currentColor" viewBox="0 0 24 24">
                      <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
                    </svg>
                  ))}
                </div>
                <p className="text-base sm:text-lg font-bold text-gray-900 mb-4 md:mb-6 text-center leading-relaxed">
                  &quot;{testimonial.text}&quot;
                </p>
                <div className="h-0.5 w-16 sm:w-20 mx-auto mb-3 md:mb-4 bg-gray-900 rounded-full" />
                <p className="text-xs sm:text-sm text-gray-600 text-center font-semibold">
                  {testimonial.author} · <span className="text-gray-400">{testimonial.days}</span>
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* FAQ Section */}
      <section className="relative py-20 md:py-32 px-4 sm:px-6 z-10 bg-gray-50">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-12 md:mb-20 scroll-animate">
            <h2 className="text-3xl sm:text-4xl md:text-5xl font-black mb-4 text-gray-900 tracking-tight">
              Questions fréquentes
            </h2>
          </div>

          <div className="space-y-3 md:space-y-4">
            {[
              {
                question: "Comment Revenux trouve-t-il les produits gagnants ?",
                answer: "Notre intelligence artificielle analyse en continu des milliers de produits digitaux sur les principales marketplaces. Nous identifions automatiquement ceux qui génèrent le plus de revenus grâce à notre algorithme propriétaire qui prend en compte la croissance, les ventes et les tendances du marché."
              },
              {
                question: "Les données sont-elles fiables et à jour ?",
                answer: "Absolument ! Chaque produit est vérifié avant d'être ajouté à notre base. Nous garantissons que toutes les images, descriptions et liens sont fonctionnels et à jour. Notre système met à jour automatiquement les données plusieurs fois par jour pour t'assurer d'avoir toujours les informations les plus récentes."
              },
              {
                question: "Puis-je utiliser ces produits pour mon business ?",
                answer: "Bien sûr ! Tous les produits que tu découvres sur Revenux sont prêts à être utilisés. Tu peux exporter toutes les données nécessaires (images, descriptions, prix) dans le format de ton choix et commencer à vendre immédiatement."
              },
              {
                question: "Quelle est la différence entre l'essai gratuit et les plans payants ?",
                answer: "L'essai gratuit te permet de découvrir 10 produits gagnants et d'explorer toutes les fonctionnalités de base. Les plans payants offrent un accès illimité à notre base de données complète, des analyses approfondies, des alertes en temps réel et un support prioritaire pour maximiser tes chances de succès."
              }
            ].map((faq, idx) => (
              <div
                key={idx}
                className="bg-white rounded-xl md:rounded-2xl p-4 md:p-6 shadow-sm hover:shadow-lg transition-all duration-300 border border-gray-100 scroll-animate cursor-pointer"
                style={{ animationDelay: `${idx * 0.1}s` }}
                onClick={() => setOpenFaq(openFaq === idx ? null : idx)}
              >
                <div className="flex items-start justify-between gap-3">
                  <h3 className="text-base sm:text-lg font-bold text-gray-900 pr-4 flex-1 leading-snug">{faq.question}</h3>
                  <svg 
                    className={`w-5 h-5 sm:w-6 sm:h-6 text-gray-600 flex-shrink-0 transition-transform duration-300 mt-0.5 ${openFaq === idx ? 'rotate-180' : ''}`}
                    fill="none" 
                    stroke="currentColor" 
                    viewBox="0 0 24 24"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </div>
                {openFaq === idx && (
                  <p className="mt-3 md:mt-4 text-sm sm:text-base text-gray-600 leading-relaxed animate-fade-in-up">
                    {faq.answer}
                  </p>
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Pricing Section */}
      <section id="tarifs" className="relative py-20 md:py-32 px-4 sm:px-6 z-10 bg-white">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-12 md:mb-20 scroll-animate">
            <h2 className="text-3xl sm:text-4xl md:text-5xl font-black mb-4 text-gray-900 tracking-tight">
              Choisis ton plan
            </h2>
            <p className="text-base md:text-lg text-gray-600 max-w-2xl mx-auto font-normal">
              Des tarifs transparents pour tous les besoins
            </p>
          </div>

          <div className="grid md:grid-cols-2 gap-4 md:gap-6 lg:gap-8 max-w-5xl mx-auto">
            {/* Plan 3 mois */}
            <div className="bg-gradient-to-br from-gray-50 to-white rounded-2xl md:rounded-3xl p-5 sm:p-6 md:p-10 shadow-lg border-2 border-gray-200 hover:border-gray-300 transition-all duration-300 hover:shadow-xl scroll-animate">
              <div className="mb-5 md:mb-6">
                <div className="inline-block bg-gray-900 text-white text-xs font-bold uppercase tracking-wider px-2 sm:px-3 py-1 rounded-full mb-3 md:mb-4">
                  3 mois
                </div>
                <h3 className="text-xl sm:text-2xl md:text-3xl font-black text-gray-900 mb-2">Plan Essentiel</h3>
                <div className="flex items-baseline gap-2 mb-3 md:mb-4">
                  <span className="text-3xl sm:text-4xl md:text-5xl font-black text-gray-900">100€</span>
                  <span className="text-gray-600 text-base sm:text-lg">/3 mois</span>
                </div>
                <div className="text-xs sm:text-sm text-gray-600 mb-2">65 595 FCFA</div>
              </div>

              <ul className="space-y-2 sm:space-y-3 mb-6 md:mb-8">
                {[
                  'Accès à la base de produits',
                  'Analyse de 50 produits/mois',
                  'Filtres de recherche de base',
                  'Export des données',
                  'Support par email'
                ].map((feature, idx) => (
                  <li key={idx} className="flex items-start gap-2 sm:gap-3">
                    <svg className="w-4 h-4 sm:w-5 sm:h-5 text-green-600 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                    <span className="text-xs sm:text-sm md:text-base text-gray-700 leading-relaxed">{feature}</span>
                  </li>
                ))}
              </ul>

              <Link href="/auth/register" className="block w-full">
                <Button className="w-full bg-gray-900 text-white hover:bg-gray-800 rounded-lg px-4 sm:px-6 py-2.5 sm:py-3 text-sm sm:text-base font-semibold shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-105">
                  Choisir ce plan
                </Button>
              </Link>
            </div>

            {/* Plan 6 mois - Popular */}
            <div className="bg-gradient-to-br from-gray-900 to-gray-800 rounded-2xl md:rounded-3xl p-5 sm:p-6 md:p-10 shadow-2xl border-2 border-gray-700 hover:border-gray-600 transition-all duration-300 hover:shadow-3xl relative scroll-animate" style={{ animationDelay: '0.1s' }}>
              <div className="absolute -top-3 sm:-top-4 left-1/2 -translate-x-1/2">
                <span className="bg-blue-600 text-white text-xs font-bold uppercase tracking-wider px-3 sm:px-4 py-1 sm:py-1.5 rounded-full shadow-lg">
                  Le plus populaire
                </span>
              </div>
              
              <div className="mb-5 md:mb-6 mt-3 sm:mt-2">
                <div className="inline-block bg-white/20 text-white text-xs font-bold uppercase tracking-wider px-2 sm:px-3 py-1 rounded-full mb-3 md:mb-4">
                  6 mois
                </div>
                <h3 className="text-xl sm:text-2xl md:text-3xl font-black text-white mb-2">Plan Premium</h3>
                <div className="flex items-baseline gap-2 mb-3 md:mb-4">
                  <span className="text-3xl sm:text-4xl md:text-5xl font-black text-white">150€</span>
                  <span className="text-gray-300 text-base sm:text-lg">/6 mois</span>
                </div>
                <div className="text-xs sm:text-sm text-gray-300 mb-2">98 393 FCFA</div>
                <div className="text-xs sm:text-sm text-green-400 font-semibold">Économise 50€ sur 6 mois</div>
              </div>

              <ul className="space-y-2 sm:space-y-3 mb-6 md:mb-8">
                {[
                  'Accès illimité à la base de produits',
                  'Analyse illimitée de produits',
                  'Tous les filtres avancés',
                  'Export prioritaire des données',
                  'Support prioritaire 24/7',
                  'Alertes en temps réel',
                  'Analyses approfondies'
                ].map((feature, idx) => (
                  <li key={idx} className="flex items-start gap-2 sm:gap-3">
                    <svg className="w-4 h-4 sm:w-5 sm:h-5 text-green-400 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                    <span className="text-xs sm:text-sm md:text-base text-white leading-relaxed">{feature}</span>
                  </li>
                ))}
              </ul>

              <Link href="/auth/register" className="block w-full">
                <Button className="w-full bg-white text-gray-900 hover:bg-gray-100 rounded-lg px-4 sm:px-6 py-2.5 sm:py-3 text-sm sm:text-base font-semibold shadow-xl hover:shadow-2xl transition-all duration-300 hover:scale-105">
                  Choisir ce plan
                </Button>
              </Link>
            </div>
          </div>

          <div className="text-center mt-6 md:mt-8 px-4">
            <p className="text-xs sm:text-sm text-gray-600">
              Tous les plans incluent l&apos;essai gratuit de 7 jours. Annule à tout moment.
            </p>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="relative py-20 md:py-32 px-4 sm:px-6 z-10 bg-gray-900 scroll-animate">
        <div className="max-w-5xl mx-auto text-center">
          <div className="bg-gradient-to-br from-gray-800 to-gray-900 rounded-2xl md:rounded-3xl p-8 md:p-12 lg:p-20 shadow-2xl border border-gray-700 hover:border-gray-600 transition-all duration-500 hover:scale-105">
            <h2 className="text-3xl sm:text-4xl md:text-5xl lg:text-6xl font-black text-white mb-4 md:mb-6 tracking-tight">
              Prêt à trouver tes produits gagnants ?
            </h2>
            <p className="text-base sm:text-lg md:text-xl text-gray-400 mb-8 md:mb-12 max-w-2xl mx-auto font-normal">
              Rejoins des milliers d&apos;entrepreneurs qui utilisent Revenux pour découvrir leurs produits digitaux gagnants
            </p>
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              <Link href="/auth/register">
                <Button className="w-full sm:w-auto bg-white text-gray-900 hover:bg-gray-100 rounded-full px-8 md:px-10 py-5 md:py-6 text-base md:text-lg font-bold shadow-2xl hover:shadow-3xl transition-all duration-300 hover:scale-110">
                  Commencer gratuitement
                </Button>
              </Link>
              <Link href="/dashboard">
                <Button className="w-full sm:w-auto bg-gray-800 border-2 border-gray-700 text-white hover:bg-gray-700 hover:border-gray-600 rounded-full px-8 md:px-10 py-5 md:py-6 text-base md:text-lg font-semibold transition-all duration-300 hover:scale-105">
                  Voir la démo
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="relative bg-gray-900 text-gray-300 py-12 md:py-20 px-4 sm:px-6 z-10 border-t border-gray-800">
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6 md:gap-8 lg:gap-12 mb-12 md:mb-16">
            <div className="space-y-3 md:space-y-4 col-span-2 md:col-span-1">
              <div className="flex items-center gap-2 sm:gap-3">
                <Logo size="sm" />
                <span className="text-lg sm:text-xl font-bold text-white">
                  Revenux
                </span>
              </div>
              <p className="text-xs sm:text-sm text-gray-400 leading-relaxed">
                Outil tout-en-un pour trouver et analyser des produits digitaux gagnants
              </p>
            </div>

            <div>
              <h4 className="font-bold text-white mb-4 md:mb-6 text-sm sm:text-base md:text-lg">Product</h4>
              <ul className="space-y-2 md:space-y-3 text-xs sm:text-sm">
                {['Top Ads', 'Top Shops', 'Top Products', 'Shop Analysis', 'Analyse de produits'].map((item) => (
                  <li key={item}>
                    <Link href="/dashboard" className="text-gray-400 hover:text-white transition-colors duration-300">
                      {item}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>

            <div>
              <h4 className="font-bold text-white mb-4 md:mb-6 text-sm sm:text-base md:text-lg">Resources</h4>
              <ul className="space-y-2 md:space-y-3 text-xs sm:text-sm">
                {['Pricing', 'Ecommerce Course', 'Live Coaching', 'Blog', 'Q&A', 'Reviews'].map((item) => (
                  <li key={item}>
                    <Link href="#" className="text-gray-400 hover:text-white transition-colors duration-300">
                      {item}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>

            <div className="col-span-2 md:col-span-1">
              <h4 className="font-bold text-white mb-4 md:mb-6 text-sm sm:text-base md:text-lg">Alternatives</h4>
              <ul className="space-y-2 md:space-y-3 text-xs sm:text-sm">
                {['Foreplay', 'Shophunter', 'Kalodata', 'Storeleads', 'Pipiads'].map((item) => (
                  <li key={item}>
                    <Link href="#" className="text-gray-400 hover:text-white transition-colors duration-300">
                      {item}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          </div>

          <div className="border-t border-gray-800 pt-6 md:pt-8 flex flex-col md:flex-row items-center justify-between gap-4 md:gap-6">
            <div className="flex flex-col sm:flex-row items-center gap-3 sm:gap-6 text-xs sm:text-sm text-gray-400">
              <span>2025 Revenux</span>
              <Link href="#" className="hover:text-white transition-colors duration-300">Privacy Policy</Link>
              <Link href="#" className="hover:text-white transition-colors duration-300">Terms of Service</Link>
            </div>

            <div className="flex items-center gap-3 md:gap-4">
              {['tiktok', 'instagram', 'linkedin'].map((social) => (
                <a
                  key={social}
                  href="#"
                  className="w-8 h-8 sm:w-10 sm:h-10 rounded-full bg-gray-800 border border-gray-700 flex items-center justify-center hover:border-white hover:text-white hover:bg-gray-700 transition-all duration-300 hover:scale-110"
                >
                  <svg className="w-4 h-4 sm:w-5 sm:h-5" fill="currentColor" viewBox="0 0 24 24">
                    {social === 'tiktok' && <path d="M19.59 6.69a4.83 4.83 0 0 1-3.77-4.25V2h-3.45v13.67a2.89 2.89 0 0 1-5.2 1.74 2.89 2.89 0 0 1 2.31-4.64 2.93 2.93 0 0 1 .88.13V9.4a6.84 6.84 0 0 0-.88-.05 6.33 6.33 0 0 0-5.23 2.82 6.34 6.34 0 0 0 10.47 6.84 6.89 6.89 0 0 0 3.48-5.64V7.5a5 5 0 0 0 4-4.81z"/>}
                    {social === 'instagram' && <path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zm0-2.163c-3.259 0-3.667.014-4.947.072-4.358.2-6.78 2.618-6.98 6.98-.059 1.281-.073 1.689-.073 4.948 0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98 1.281.058 1.689.072 4.948.072 3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98-1.281-.059-1.69-.073-4.949-.073zm0 5.838c-3.403 0-6.162 2.759-6.162 6.162s2.759 6.163 6.162 6.163 6.162-2.759 6.162-6.163c0-3.403-2.759-6.162-6.162-6.162zm0 10.162c-2.209 0-4-1.79-4-4 0-2.209 1.791-4 4-4s4 1.791 4 4c0 2.21-1.791 4-4 4zm6.406-11.845c-.796 0-1.441.645-1.441 1.44s.645 1.44 1.441 1.44c.795 0 1.439-.645 1.439-1.44s-.644-1.44-1.439-1.44z"/>}
                    {social === 'linkedin' && <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/>}
                  </svg>
                </a>
              ))}
            </div>

            <div className="flex items-center gap-2">
              {['FR', 'EN', 'ES'].map((lang, idx) => (
                <button
                  key={lang}
                  className={`px-3 sm:px-4 py-1.5 sm:py-2 rounded-lg text-xs sm:text-sm font-medium transition-all duration-300 ${
                    idx === 0
                      ? 'bg-white text-gray-900 shadow-lg hover:scale-105'
                      : 'text-gray-400 hover:text-white bg-gray-800 border border-gray-700 hover:scale-105'
                  }`}
                >
                  {lang}
                </button>
              ))}
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}

