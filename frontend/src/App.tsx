import { useEffect, useMemo, useRef, useState, type ReactNode } from 'react'
import './App.css'
import tg from './shared/telegram'
import {
  createInvoice,
  createMiniAppSession,
  fetchPaymentMethods,
  fetchPaymentProducts,
  openPaymentLink,
  type PaymentMethod,
  type PaymentProduct,
} from './shared/api'

type MethodBadge = {
  logo: ReactNode
}

const CardRuLogo = () => (
  <svg width="40" height="40" viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg">
    <rect width="40" height="40" rx="20" fill="black" />
    <path d="M15.9997 30.3346V11.668H23.9997C25.0605 11.668 26.078 12.0894 26.8281 12.8395C27.5782 13.5897 27.9997 14.6071 27.9997 15.668C27.9997 16.7288 27.5782 17.7463 26.8281 18.4964C26.078 19.2465 25.0605 19.668 23.9997 19.668H13.333" stroke="white" strokeWidth="2.66667" strokeLinecap="round" strokeLinejoin="round" />
    <path d="M23.9997 25H13.333" stroke="white" strokeWidth="2.66667" strokeLinecap="round" strokeLinejoin="round" />
  </svg>
)

type PlanType = 'base' | 'optimal' | 'premium'

const SbpLogo = () => (
  <svg width="40" height="40" viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg">
    <g clipPath="url(#clip0_sbp)">
      <path d="M4 8.70654L8.79406 17.3649V22.6462L4.00561 31.2875L4 8.70654Z" fill="#5B57A2" />
      <path d="M22.4082 14.2145L26.9004 11.4325L36.094 11.4238L22.4082 19.8952V14.2145Z" fill="#D90751" />
      <path d="M22.3814 8.65567L22.4068 20.119L17.6016 17.1357V0L22.3814 8.65567Z" fill="#FAB718" />
      <path d="M36.0926 11.4237L26.8987 11.4323L22.3814 8.65567L17.6016 0L36.0926 11.4237Z" fill="#ED6F26" />
      <path d="M22.4068 31.3355V25.7738L17.6016 22.8472L17.6042 39.9998L22.4068 31.3355Z" fill="#63B22F" />
      <path d="M26.8882 28.5789L8.79373 17.3649L4 8.70654L36.0736 28.5675L26.8882 28.5789Z" fill="#1487C9" />
      <path d="M17.6055 40.0002L22.4074 31.3359L26.8884 28.5792L36.0738 28.5679L17.6055 40.0002Z" fill="#017F36" />
      <path d="M4.00586 31.2879L17.6415 22.8479L13.0572 20.0059L8.79431 22.6465L4.00586 31.2879Z" fill="#984995" />
    </g>
    <defs>
      <clipPath id="clip0_sbp">
        <rect width="32" height="40" fill="white" transform="translate(4)" />
      </clipPath>
    </defs>
  </svg>
)

const CardIntlLogo = () => (
  <svg width="40" height="40" viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M20 40C31.0457 40 40 31.0457 40 20C40 8.95429 31.0457 0 20 0C8.95429 0 0 8.95429 0 20C0 31.0457 8.95429 40 20 40Z" fill="white" />
    <g clipPath="url(#clip0_cardintl)">
      <path d="M22.7155 14.5352H16.4434V25.8037H22.7155V14.5352Z" fill="#FF5A00" />
      <path d="M16.8608 20.1675C16.8608 17.8781 17.9371 15.8461 19.5887 14.5332C18.3732 13.5776 16.8399 13 15.1675 13C11.2057 13 8 16.2057 8 20.1675C8 24.1294 11.2057 27.3351 15.1675 27.3351C16.8399 27.3351 18.3732 26.7575 19.5887 25.8018C17.9348 24.5075 16.8608 22.457 16.8608 20.1675Z" fill="#EB001B" />
      <path d="M31.1785 20.1675C31.1785 24.1294 27.9728 27.3351 24.011 27.3351C22.3386 27.3351 20.8053 26.7575 19.5898 25.8018C21.2623 24.4866 22.3177 22.457 22.3177 20.1675C22.3177 17.8781 21.2414 15.8461 19.5898 14.5332C20.803 13.5776 22.3362 13 24.0087 13C27.9728 13 31.1785 16.2265 31.1785 20.1675Z" fill="#F79E1B" />
    </g>
    <defs>
      <clipPath id="clip0_cardintl"><rect width="23.1773" height="18" fill="white" transform="translate(8 11)" /></clipPath>
    </defs>
  </svg>
)

const CryptoLogo = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="40" height="40" viewBox="0 0 40 40" fill="none">
    <circle cx="20" cy="20" r="20" fill="#26A17B" />
    <path d="M22.412 21.066v-.002c-.13.01-.8.05-2.29.05-1.19 0-2.03-.036-2.324-.05v.002c-4.59-.202-8.017-.999-8.017-1.96 0-.96 3.427-1.758 8.017-1.963v3.128c.298.021 1.156.073 2.344.073 1.422 0 2.134-.06 2.27-.073v-3.127c4.581.205 8 1.003 8 1.962 0 .96-3.419 1.757-8 1.96zm0-4.25v-2.8h6.394V10H11.19v4.016h6.395v2.8C12.4 17.056 8 18.075 8 19.305c0 1.23 4.4 2.248 9.585 2.49v8.922h4.827v-8.924C27.596 21.55 32 20.534 32 19.306c0-1.23-4.404-2.25-9.588-2.49z" fill="white" />
  </svg>
)

const StarsLogo = () => (
  <svg width="40" height="40" viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg">
    <circle cx="20" cy="20" r="20" fill="#FBC01C" />
    <path d="M20 10l2.2 5.9 6.3.2-5 3.8 1.8 6.1-5.3-3.5-5.3 3.5 1.8-6.1-5-3.8 6.3-.2L20 10z" fill="white" />
  </svg>
)

const PayPalLogo = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="40" height="40" viewBox="0 0 64 64">
    <path fill="#139AD6" d="M49.2 28.2h-3.4c-.2 0-.4.2-.5.4l-1.4 8.8c0 .2.1.3.3.3H46c.2 0 .3-.1.3-.3l.4-2.5c0-.2.2-.4.5-.4h1.1c2.3 0 3.6-1.1 3.9-3.3.2-.9 0-1.7-.4-2.2-.6-.5-1.5-.8-2.6-.8m.4 3.3c-.2 1.2-1.1 1.2-2 1.2H47l.4-2.3c0-.1.1-.2.3-.2h.2c.6 0 1.2 0 1.5.4.2.1.2.4.2.9" />
    <path fill="#263B80" d="M24.7 28.2h-3.4c-.2 0-.4.2-.5.4l-1.4 8.8c0 .2.1.3.3.3h1.6c.2 0 .4-.2.5-.4l.4-2.4c0-.2.2-.4.5-.4h1.1c2.3 0 3.6-1.1 3.9-3.3.2-.9 0-1.7-.4-2.2-.6-.5-1.4-.8-2.6-.8m.4 3.3c-.2 1.2-1.1 1.2-2 1.2h-.5l.4-2.3c0-.1.1-.2.3-.2h.2c.6 0 1.2 0 1.5.4.1.1.2.4.1.9M35 31.4h-1.6c-.1 0-.3.1-.3.2l-.1.5-.1-.2c-.4-.5-1.1-.7-1.9-.7-1.8 0-3.4 1.4-3.7 3.3-.2 1 .1 1.9.6 2.5.5.6 1.2.8 2.1.8 1.5 0 2.3-.9 2.3-.9l-.1.5c0 .2.1.3.3.3H34c.2 0 .4-.2.5-.4l.9-5.6c-.1-.1-.3-.3-.4-.3m-2.3 3.2c-.2.9-.9 1.6-1.9 1.6-.5 0-.9-.2-1.1-.4-.2-.3-.3-.7-.3-1.2.1-.9.9-1.6 1.8-1.6.5 0 .8.2 1.1.4.3.3.4.8.4 1.2" />
    <path fill="#139AD6" d="M59.4 31.4h-1.6c-.1 0-.3.1-.3.2l-.1.5-.1-.2c-.4-.5-1.1-.7-1.9-.7-1.8 0-3.4 1.4-3.7 3.3-.2 1 .1 1.9.6 2.5.5.6 1.2.8 2.1.8 1.5 0 2.3-.9 2.3-.9l-.1.5c0 .2.1.3.3.3h1.5c.2 0 .4-.2.5-.4l.9-5.6c-.1-.1-.2-.3-.4-.3m-2.3 3.2c-.2.9-.9 1.6-1.9 1.6-.5 0-.9-.2-1.1-.4-.2-.3-.3-.7-.3-1.2.1-.9.9-1.6 1.8-1.6.5 0 .8.2 1.1.4.4.3.5.8.4 1.2" />
    <path fill="#263B80" d="M43.7 31.4H42c-.2 0-.3.1-.4.2L39.4 35l-1-3.2c-.1-.2-.2-.3-.5-.3h-1.6c-.2 0-.3.2-.3.4l1.8 5.3-1.7 2.4c-.1.2 0 .5.2.5h1.6c.2 0 .3-.1.4-.2l5.5-7.9c.3-.3.1-.6-.1-.6" />
    <path fill="#139AD6" d="m61.3 28.5-1.4 9c0 .2.1.3.3.3h1.4c.2 0 .4-.2.5-.4l1.4-8.8c0-.2-.1-.3-.3-.3h-1.6c-.1-.1-.2 0-.3.2" />
    <path fill="#263B80" d="M12 25.2c-.7-.8-2-1.2-3.8-1.2h-5c-.3 0-.6.3-.7.6l-2 13.1c0 .3.2.5.4.5H4l.8-4.9v.2c.1-.3.4-.6.7-.6H7c2.9 0 5.1-1.2 5.8-4.5v-.3c-.1 0-.1 0 0 0 .1-1.3-.1-2.1-.8-2.9" />
    <path fill="#139AD6" d="M12.7 28.1v.3c-.7 3.4-2.9 4.5-5.8 4.5H5.4c-.3 0-.6.3-.7.6l-1 6.1c0 .2.1.4.4.4h2.6c.3 0 .6-.2.6-.5v-.1l.5-3.1v-.2c0-.3.3-.5.6-.5h.4c2.5 0 4.5-1 5-4 .2-1.2.1-2.3-.5-3-.1-.2-.3-.4-.6-.5" />
    <path fill="#232C65" d="M12 27.8c-.1 0-.2-.1-.3-.1-.1 0-.2 0-.3-.1-.4-.1-.8-.1-1.3-.1H6.2c-.1 0-.2 0-.3.1-.2.1-.3.3-.3.5l-.8 5.2v.2c.1-.3.4-.6.7-.6H7c2.9 0 5.1-1.2 5.8-4.5 0-.1 0-.2.1-.3-.2-.1-.3-.2-.5-.2-.3-.1-.3-.1-.4-.1" />
  </svg>
)

const GenericMethodLogo = () => (
  <svg width="40" height="40" viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg">
    <circle cx="20" cy="20" r="20" fill="#2A3142" />
    <rect x="11" y="13" width="18" height="14" rx="3" stroke="white" strokeOpacity="0.85" strokeWidth="2" />
    <path d="M11 18H29" stroke="white" strokeOpacity="0.85" strokeWidth="2" />
  </svg>
)

const METHOD_DISPLAY: Record<string, { title: string; badge: MethodBadge; isNew?: boolean }> = {
  CARD_RU: { title: 'Российская карта', badge: { logo: <CardRuLogo /> } },
  CARD_INTERNATIONAL: { title: 'Иностранная карта', badge: { logo: <CardIntlLogo /> } },
  SBP: { title: 'Система быстрых платежей', badge: { logo: <SbpLogo /> } },
  CRYPTO: { title: 'Криптовалюта', badge: { logo: <CryptoLogo /> } },
  CRYPTO_NOWPAYMENTS: { title: 'Криптовалюта', badge: { logo: <CryptoLogo /> } },
  PAYPAL: { title: 'PayPal', badge: { logo: <PayPalLogo /> } },
  TELEGRAM_STARS: { title: 'Telegram Stars', badge: { logo: <StarsLogo /> } },
}

const METHOD_CODE_ALIASES: Record<string, string> = {
  CARD: 'CARD_RU',
  RU_CARD: 'CARD_RU',
  CARD_RUS: 'CARD_RU',
  FAST_PAYMENT_SYSTEM: 'SBP',
  FPS: 'SBP',
  INTERNATIONAL_CARD: 'CARD_INTERNATIONAL',
  CARD_INTL: 'CARD_INTERNATIONAL',
}

function normalizeMethodCode(code: string): string {
  const normalized = code.trim().toUpperCase()
  return METHOD_CODE_ALIASES[normalized] ?? normalized
}

function formatRub(value: number): string {
  return new Intl.NumberFormat('ru-RU').format(value)
}

function parseNumeric(value: string | number): number {
  return typeof value === 'number' ? value : Number(value)
}

function getMethodDisplay(method: PaymentMethod): { title: string; badge: MethodBadge; isNew?: boolean } {
  const normalizedCode = normalizeMethodCode(method.code)
  return (
    METHOD_DISPLAY[normalizedCode] ?? {
      title: normalizedCode.replaceAll('_', ' '),
      badge: { logo: <GenericMethodLogo /> },
    }
  )
}

function getPlanType(planName: string): PlanType {
  const lowerName = planName.toLowerCase()

  const isPremium =
    lowerName.includes('premium') ||
    lowerName.includes('премиум') ||
    lowerName.includes('prem')

  if (isPremium) return 'premium'

  const isOptimal =
    lowerName.includes('optimal') ||
    lowerName.includes('optimalnyy') ||
    lowerName.includes('оптим')

  if (isOptimal) return 'optimal'

  return 'base'
}

function getPlanAccentLabel(planType: PlanType): string {
  if (planType === 'premium') return 'Максимум возможностей'
  if (planType === 'optimal') return 'Лучший баланс'
  return 'Стартовый выбор'
}

function isProductionLikeStand(): boolean {
  return String(import.meta.env.VITE_STAND || '').trim() === 'production'
}

function getPlanInfoItems(plan: PaymentProduct, planType: PlanType): string[] {
  const llmLimit = plan.llm_max_limit ?? 0
  const imageLimit = plan.image_max_limit ?? 0
  const videoLimit = plan.video_max_limit ?? 0

  const items = [
    `${new Intl.NumberFormat('ru-RU').format(parseNumeric(plan.tokens_amount))} токенов`,
    'Доступ ко всем моделям AI',
    `Лимит LLM: ${new Intl.NumberFormat('ru-RU').format(llmLimit)} запросов`,
    `Лимит изображений: ${new Intl.NumberFormat('ru-RU').format(imageLimit)} запросов`,
    `Лимит видео: ${new Intl.NumberFormat('ru-RU').format(videoLimit)} запросов`,
  ]

  if (planType === 'premium') {
    items.push('VPN-бонус за первую покупку')
  }

  return items
}

function App() {
  const carouselRef = useRef<HTMLDivElement>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [products, setProducts] = useState<PaymentProduct[]>([])
  const [methods, setMethods] = useState<PaymentMethod[]>([])
  const [selectedPlanId, setSelectedPlanId] = useState<string | null>(null)
  const [selectedMethod, setSelectedMethod] = useState<string | null>(null)
  const [isMethodsListOpen, setIsMethodsListOpen] = useState(false)
  const selectedPlan = useMemo(
    () => products.find((plan) => plan.plan_id === selectedPlanId) ?? null,
    [products, selectedPlanId],
  )

  const selectedPlanType = useMemo(
    () => (selectedPlan ? getPlanType(selectedPlan.display_name) : 'base'),
    [selectedPlan],
  )

  const selectedMethodObj = useMemo(
    () => methods.find((m) => m.code === selectedMethod) ?? null,
    [methods, selectedMethod],
  )

  const handlePlanSelect = (planId: string) => {
    setSelectedPlanId(planId)

    const carousel = carouselRef.current
    if (!carousel) return

    const selectedButton = carousel.querySelector(`[data-plan-id="${planId}"]`) as HTMLElement | null
    selectedButton?.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' })
  }

  useEffect(() => {
    tg.ready()
    tg.expand()
    tg.disableVerticalSwipes()
    tg.setHeaderColor('#000000')
    tg.setBackgroundColor('#0a0c0d')

    const isProdStand = isProductionLikeStand()
    const liveInitData = String(tg.initData || '').trim()
    const devInitDataMock = String(import.meta.env.VITE_INIT_DATA || '').trim()
    const initData = isProdStand ? liveInitData : liveInitData || devInitDataMock

    if (!initData) {
      setError('Telegram init_data is missing. Open this page from Telegram Mini App.')
      setIsLoading(false)
      return
    }

    const bootstrap = async () => {
      try {
        await createMiniAppSession(initData)
        const [productsData, methodsData] = await Promise.all([
          fetchPaymentProducts(),
          fetchPaymentMethods(),
        ])
        setProducts(productsData)
        setMethods(methodsData)
        setSelectedPlanId(productsData[0]?.plan_id ?? null)
        const defaultMethod = methodsData.find((method) => method.enabled && !method.is_soon)
        setSelectedMethod(defaultMethod?.code ?? null)
      } catch (fetchError) {
        const message = fetchError instanceof Error ? fetchError.message : 'Failed to initialize payment page'
        setError(message)
      } finally {
        setIsLoading(false)
      }
    }

    void bootstrap()
  }, [])

  // Auto-select plan based on carousel scroll position
  useEffect(() => {
    const carousel = carouselRef.current
    if (!carousel || !products.length) return

    const handleCarouselScroll = () => {
      let closestPlanId: string | null = null
      let closestDistance = Infinity

      products.forEach((product) => {
        const button = carousel.querySelector(`[data-plan-id="${product.plan_id}"]`) as HTMLElement
        if (!button) return

        const rect = button.getBoundingClientRect()
        const carouselRect = carousel.getBoundingClientRect()
        const buttonCenterX = rect.left - carouselRect.left + rect.width / 2
        const distance = Math.abs(buttonCenterX - carousel.clientWidth / 2)

        if (distance < closestDistance) {
          closestDistance = distance
          closestPlanId = product.plan_id
        }
      })

      if (closestPlanId) {
        setSelectedPlanId(closestPlanId)
      }
    }

    carousel.addEventListener('scroll', handleCarouselScroll)
    return () => carousel.removeEventListener('scroll', handleCarouselScroll)
  }, [products])

  const handlePay = async () => {
    if (!selectedPlanId || !selectedMethod) {
      setError('Выберите тариф и способ оплаты.')
      return
    }

    setIsSubmitting(true)
    setError(null)
    try {
      const invoice = await createInvoice(selectedPlanId, selectedMethod)
      if (!invoice.payment_url) {
        throw new Error('Payment URL is not returned by provider')
      }
      openPaymentLink(invoice.payment_url)
    } catch (invoiceError) {
      const message = invoiceError instanceof Error ? invoiceError.message : 'Failed to create invoice'
      setError(message)
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <main className={`payment-page payment-page--${selectedPlanType}`}>
      {isLoading && <div className="placeholder">Loading plans...</div>}

      {!isLoading && (
        <>
          {/* ЗАГОЛОВОК */}
          <div className="payment-header">
            <h1 className="payment-title">Выберите тариф</h1>
            <p className="payment-subtitle">Пополняйте баланс токенов и получайте доступ к самым лучшим моделям</p>
          </div>

          {/* БОЛЬШИЕ КАРТОЧКИ ПЛАНОВ - КАРУСЕЛЬ/GRID */}
          <div className="plans-carousel" ref={carouselRef}>
            {products.map((plan) => {
              const isSelected = selectedPlanId === plan.plan_id
              const planType = getPlanType(plan.display_name)
              const planInfoItems = getPlanInfoItems(plan, planType)
              return (
                <button
                  key={plan.plan_id}
                  type="button"
                  data-plan-id={plan.plan_id}
                  className={`plan-large plan-large--${planType} ${isSelected ? 'plan-large--active' : ''}`}
                  onClick={() => handlePlanSelect(plan.plan_id)}
                >
                  <div className="plan-large-header">
                    <div className="plan-large-heading-wrap">
                      <span className={`plan-large-accent plan-large-accent--${planType}`}>{getPlanAccentLabel(planType)}</span>
                      <h2 className="plan-large-name">{plan.display_name}</h2>
                    </div>
                    {isSelected && (
                      <div className="plan-large-check">
                        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none">
                          <path fillRule="evenodd" clipRule="evenodd" d="M12 0C5.37258 0 0 5.37258 0 12C0 18.6274 5.37258 24 12 24C18.6274 24 24 18.6274 24 12C24 5.37258 18.6274 0 12 0ZM11.1107 17.4719L18.4 8.1L16.9 6.93333L10.8873 14.664L6.8966 10.9393L5.6 12.3286L11.1107 17.4719Z" fill="white" />
                        </svg>
                      </div>
                    )}
                  </div>

                  <div className="plan-large-price">
                    <span className="plan-large-price-value">{formatRub(parseNumeric(plan.price_rub))}</span>
                    <span className="plan-large-price-currency">RUB</span>
                  </div>

                  <ul className="plan-info-list" aria-label="Информация о тарифе">
                    {planInfoItems.map((item) => (
                      <li key={item} className="plan-info-item">
                        <svg className="plan-info-check" xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none">
                          <path d="M20 6L9 17L4 12" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" />
                        </svg>
                        <span>{item}</span>
                      </li>
                    ))}
                  </ul>
                </button>
              )
            })}
          </div>

          {/* МЕТОДЫ ОПЛАТЫ - РАСКРЫВАЮЩИЙСЯ СПИСОК */}
          <div className="payment-methods-section">
            {selectedPlan && (
              <div className="selected_plan_row">
                <span>Вы выбрали:</span>
                <strong>
                  {selectedPlan.display_name} • {formatRub(parseNumeric(selectedPlan.price_rub))} RUB
                </strong>
              </div>
            )}

            <button
              type="button"
              className="payment-methods-toggle"
              onClick={() => setIsMethodsListOpen(!isMethodsListOpen)}
            >
              <span className="payment-methods-label">Способ оплаты:</span>
              {selectedMethodObj && (
                <span className="payment-methods-selected">
                  <span className="method-logo">
                    {getMethodDisplay(selectedMethodObj).badge.logo}
                  </span>
                  <span className="method-title">{getMethodDisplay(selectedMethodObj).title}</span>
                </span>
              )}
              {!selectedMethodObj && (
                <span className="payment-methods-placeholder">Выберите способ</span>
              )}
              <svg className={`toggle-icon ${isMethodsListOpen ? 'toggle-icon--open' : ''}`} xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none">
                <path d="M6 9l6 6 6-6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </button>

            {isMethodsListOpen && (
              <div className="payment-methods-dropdown">
                {methods.map((method) => {
                  const isDisabled = !method.enabled || method.is_soon
                  const isSelected = selectedMethod === method.code
                  const display = getMethodDisplay(method)
                  return (
                    <button
                      key={method.code}
                      type="button"
                      className={[
                        'payment_item',
                        isSelected ? 'active_payment_item' : '',
                        isDisabled ? 'payment_item_soon' : '',
                      ].join(' ')}
                      disabled={isDisabled}
                      onClick={() => {
                        setSelectedMethod(method.code)
                        setIsMethodsListOpen(false)
                      }}
                    >
                      {method.is_soon && <span className="badge_soon">Soon</span>}
                      {display.isNew && !isSelected && !method.is_soon && <span className="badge_new">NEW</span>}
                      <span className="payments_name">
                        <span className="method_logo">
                          {display.badge.logo}
                        </span>
                        <p>{display.title}</p>
                      </span>
                    </button>
                  )
                })}
              </div>
            )}

            {error && <p className="error-text">{error}</p>}
          </div>

          {/* КНОПКА ОПЛАТИТЬ - ФИКСИРОВАНА ВНИЗУ */}
          <div className="payment-footer">
            <button
              type="button"
              className={`pay-button pay-button--large ${selectedPlan ? `pay-button--${getPlanType(selectedPlan.display_name)}` : ''}`}
              disabled={!selectedPlanId || !selectedMethod || isSubmitting}
              onClick={handlePay}
            >
              {isSubmitting ? 'Создаем инвойс...' : 'Оплатить'}
            </button>
          </div>

          {/* ПРОЦЕСС ОПЛАТЫ */}
          {isSubmitting && (
            <div className="payment_process" role="status" aria-live="polite">
              <div className="loader_wrapper">
                <div className="loader" />
              </div>
              <div className="payment_process_cards">
                <div className="payment_process_cards_items">
                  <div className="payment_process_cards_item">
                    <span className="card_chip card_chip_visa">VISA</span>
                  </div>
                  <div className="payment_process_cards_item">
                    <span className="card_chip card_chip_mc">MC</span>
                  </div>
                  <div className="payment_process_cards_item">
                    <span className="card_chip card_chip_crypto">USDT</span>
                  </div>
                </div>
                <p className="secure-hint">Secure payment</p>
              </div>
            </div>
          )}
        </>
      )}
    </main>
  )
}

export default App
