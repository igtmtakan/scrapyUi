import { Template } from './types'
import { basicTemplates } from './basic'
import { amazonTemplates, rakutenTemplates, yahooShoppingTemplates } from './ecommerce'
import { playwrightTemplates } from './playwright'
import { puppeteerTemplates } from './puppeteer/puppeteerTemplates'
import { gurunaviTemplates } from './food'
import { yahooNewsTemplates } from './news'
import { securityTemplates } from './security'
import { parsingTemplates } from './parsing/parsingTemplates'
import { browserAutomationTemplates } from './browser-automation/browserAutomationTemplates'

// 全テンプレートを統合
export const allTemplates: Template[] = [
  ...basicTemplates,
  ...amazonTemplates,
  ...rakutenTemplates,
  ...yahooShoppingTemplates,
  ...playwrightTemplates,
  ...puppeteerTemplates,
  ...gurunaviTemplates,
  ...yahooNewsTemplates,
  ...securityTemplates,
  ...parsingTemplates,
  ...browserAutomationTemplates,
]

// 型定義とカテゴリもエクスポート
export type { Template } from './types'
export { CATEGORIES } from './types'

// カテゴリ別テンプレートもエクスポート
export { basicTemplates } from './basic'
export { amazonTemplates, rakutenTemplates, yahooShoppingTemplates } from './ecommerce'
export { playwrightTemplates } from './playwright'
export { puppeteerTemplates } from './puppeteer/puppeteerTemplates'
export { gurunaviTemplates } from './food'
export { yahooNewsTemplates } from './news'
export { securityTemplates } from './security'
export { parsingTemplates } from './parsing/parsingTemplates'
export { browserAutomationTemplates } from './browser-automation/browserAutomationTemplates'
