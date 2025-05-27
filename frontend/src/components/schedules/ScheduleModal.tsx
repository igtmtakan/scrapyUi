'use client'

import React, { useState, useEffect } from 'react'
import { X, Clock, AlertCircle, CheckCircle, Info } from 'lucide-react'
import { Schedule, ScheduleCreate, ScheduleUpdate, Project, Spider, scheduleService } from '@/services/scheduleService'

interface ScheduleModalProps {
  isOpen: boolean
  onClose: () => void
  onSave: (schedule: Schedule) => void
  schedule?: Schedule
  mode: 'create' | 'edit'
}

export default function ScheduleModal({ isOpen, onClose, onSave, schedule, mode }: ScheduleModalProps) {
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    cron_expression: '',
    project_id: '',
    spider_id: '',
    is_active: true,
    settings: {}
  })
  
  const [projects, setProjects] = useState<Project[]>([])
  const [spiders, setSpiders] = useState<Spider[]>([])
  const [loading, setLoading] = useState(false)
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [cronValidation, setCronValidation] = useState<{ isValid: boolean; error?: string }>({ isValid: true })
  const [showCronTemplates, setShowCronTemplates] = useState(false)

  // フォームデータの初期化
  useEffect(() => {
    if (schedule && mode === 'edit') {
      setFormData({
        name: schedule.name,
        description: schedule.description || '',
        cron_expression: schedule.cron_expression,
        project_id: schedule.project_id,
        spider_id: schedule.spider_id,
        is_active: schedule.is_active,
        settings: schedule.settings || {}
      })
    } else {
      setFormData({
        name: '',
        description: '',
        cron_expression: '',
        project_id: '',
        spider_id: '',
        is_active: true,
        settings: {}
      })
    }
  }, [schedule, mode])

  // プロジェクト一覧の取得
  useEffect(() => {
    if (isOpen) {
      loadProjects()
    }
  }, [isOpen])

  // プロジェクト変更時にスパイダー一覧を更新
  useEffect(() => {
    if (formData.project_id) {
      loadSpiders(formData.project_id)
    } else {
      setSpiders([])
      setFormData(prev => ({ ...prev, spider_id: '' }))
    }
  }, [formData.project_id])

  // Cron式の検証
  useEffect(() => {
    if (formData.cron_expression) {
      const validation = scheduleService.validateCronExpression(formData.cron_expression)
      setCronValidation(validation)
    } else {
      setCronValidation({ isValid: true })
    }
  }, [formData.cron_expression])

  const loadProjects = async () => {
    try {
      const projectList = await scheduleService.getProjects()
      setProjects(projectList)
    } catch (error) {
      console.error('Failed to load projects:', error)
    }
  }

  const loadSpiders = async (projectId: string) => {
    try {
      const spiderList = await scheduleService.getSpiders(projectId)
      setSpiders(spiderList)
    } catch (error) {
      console.error('Failed to load spiders:', error)
    }
  }

  const handleInputChange = (field: string, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }))
    
    // エラーをクリア
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: '' }))
    }
  }

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {}

    if (!formData.name.trim()) {
      newErrors.name = 'スケジュール名は必須です'
    }

    if (!formData.cron_expression.trim()) {
      newErrors.cron_expression = 'Cron式は必須です'
    } else if (!cronValidation.isValid) {
      newErrors.cron_expression = cronValidation.error || 'Cron式が正しくありません'
    }

    if (!formData.project_id) {
      newErrors.project_id = 'プロジェクトを選択してください'
    }

    if (!formData.spider_id) {
      newErrors.spider_id = 'スパイダーを選択してください'
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSave = async () => {
    if (!validateForm()) return

    setLoading(true)
    try {
      let savedSchedule: Schedule

      if (mode === 'create') {
        const createData: ScheduleCreate = {
          name: formData.name,
          description: formData.description || undefined,
          cron_expression: formData.cron_expression,
          project_id: formData.project_id,
          spider_id: formData.spider_id,
          is_active: formData.is_active,
          settings: formData.settings
        }
        savedSchedule = await scheduleService.createSchedule(createData)
      } else {
        const updateData: ScheduleUpdate = {
          name: formData.name,
          description: formData.description || undefined,
          cron_expression: formData.cron_expression,
          is_active: formData.is_active,
          settings: formData.settings
        }
        savedSchedule = await scheduleService.updateSchedule(schedule!.id, updateData)
      }

      onSave(savedSchedule)
      onClose()
    } catch (error: any) {
      console.error('Failed to save schedule:', error)
      setErrors({ general: error.response?.data?.detail || 'スケジュールの保存に失敗しました' })
    } finally {
      setLoading(false)
    }
  }

  const handleCronTemplateSelect = (cronExpression: string) => {
    handleInputChange('cron_expression', cronExpression)
    setShowCronTemplates(false)
  }

  const cronTemplates = scheduleService.getCronTemplates()

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-center justify-center min-h-screen px-4">
        <div className="fixed inset-0 bg-black opacity-50" onClick={onClose}></div>
        
        <div className="relative bg-gray-800 rounded-lg p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
          {/* ヘッダー */}
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-xl font-semibold">
              {mode === 'create' ? 'スケジュール作成' : 'スケジュール編集'}
            </h3>
            <button
              onClick={onClose}
              className="p-2 text-gray-400 hover:text-white transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* エラーメッセージ */}
          {errors.general && (
            <div className="mb-4 p-3 bg-red-900/50 border border-red-500 rounded-lg flex items-center space-x-2">
              <AlertCircle className="w-5 h-5 text-red-400" />
              <span className="text-red-300">{errors.general}</span>
            </div>
          )}

          {/* フォーム */}
          <div className="space-y-6">
            {/* スケジュール名 */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                スケジュール名 <span className="text-red-400">*</span>
              </label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => handleInputChange('name', e.target.value)}
                className={`w-full px-3 py-2 bg-gray-700 border rounded-lg text-white ${
                  errors.name ? 'border-red-500' : 'border-gray-600'
                }`}
                placeholder="例: 毎日のニュース収集"
              />
              {errors.name && (
                <p className="mt-1 text-sm text-red-400">{errors.name}</p>
              )}
            </div>

            {/* 説明 */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                説明
              </label>
              <textarea
                value={formData.description}
                onChange={(e) => handleInputChange('description', e.target.value)}
                className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white"
                placeholder="スケジュールの詳細説明"
                rows={3}
              />
            </div>

            {/* プロジェクト選択 */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                プロジェクト <span className="text-red-400">*</span>
              </label>
              <select
                value={formData.project_id}
                onChange={(e) => handleInputChange('project_id', e.target.value)}
                className={`w-full px-3 py-2 bg-gray-700 border rounded-lg text-white ${
                  errors.project_id ? 'border-red-500' : 'border-gray-600'
                }`}
                disabled={mode === 'edit'}
              >
                <option value="">プロジェクトを選択</option>
                {projects.map(project => (
                  <option key={project.id} value={project.id}>
                    {project.name}
                  </option>
                ))}
              </select>
              {errors.project_id && (
                <p className="mt-1 text-sm text-red-400">{errors.project_id}</p>
              )}
            </div>

            {/* スパイダー選択 */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                スパイダー <span className="text-red-400">*</span>
              </label>
              <select
                value={formData.spider_id}
                onChange={(e) => handleInputChange('spider_id', e.target.value)}
                className={`w-full px-3 py-2 bg-gray-700 border rounded-lg text-white ${
                  errors.spider_id ? 'border-red-500' : 'border-gray-600'
                }`}
                disabled={!formData.project_id || mode === 'edit'}
              >
                <option value="">スパイダーを選択</option>
                {spiders.map(spider => (
                  <option key={spider.id} value={spider.id}>
                    {spider.name}
                  </option>
                ))}
              </select>
              {errors.spider_id && (
                <p className="mt-1 text-sm text-red-400">{errors.spider_id}</p>
              )}
            </div>

            {/* Cron式 */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Cron式 <span className="text-red-400">*</span>
              </label>
              <div className="space-y-2">
                <div className="flex space-x-2">
                  <input
                    type="text"
                    value={formData.cron_expression}
                    onChange={(e) => handleInputChange('cron_expression', e.target.value)}
                    className={`flex-1 px-3 py-2 bg-gray-700 border rounded-lg text-white ${
                      errors.cron_expression ? 'border-red-500' : 'border-gray-600'
                    }`}
                    placeholder="0 6 * * *"
                  />
                  <button
                    type="button"
                    onClick={() => setShowCronTemplates(!showCronTemplates)}
                    className="px-3 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors"
                  >
                    <Clock className="w-4 h-4" />
                  </button>
                </div>
                
                {/* Cron式の説明 */}
                {formData.cron_expression && cronValidation.isValid && (
                  <div className="flex items-center space-x-2 text-sm text-green-400">
                    <CheckCircle className="w-4 h-4" />
                    <span>{scheduleService.formatCronExpression(formData.cron_expression)}</span>
                  </div>
                )}
                
                {errors.cron_expression && (
                  <p className="text-sm text-red-400">{errors.cron_expression}</p>
                )}
                
                {/* Cronテンプレート */}
                {showCronTemplates && (
                  <div className="bg-gray-700 border border-gray-600 rounded-lg p-3">
                    <h4 className="text-sm font-medium text-gray-300 mb-2">よく使用されるパターン</h4>
                    <div className="grid grid-cols-1 gap-1 max-h-40 overflow-y-auto">
                      {cronTemplates.map((template, index) => (
                        <button
                          key={index}
                          type="button"
                          onClick={() => handleCronTemplateSelect(template.value)}
                          className="text-left px-2 py-1 text-sm hover:bg-gray-600 rounded transition-colors"
                        >
                          <div className="flex justify-between">
                            <span className="text-white">{template.label}</span>
                            <span className="text-gray-400 font-mono">{template.value}</span>
                          </div>
                          <div className="text-xs text-gray-500">{template.description}</div>
                        </button>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* アクティブ状態 */}
            <div>
              <label className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  checked={formData.is_active}
                  onChange={(e) => handleInputChange('is_active', e.target.checked)}
                  className="w-4 h-4 text-blue-600 bg-gray-700 border-gray-600 rounded"
                />
                <span className="text-sm text-gray-300">スケジュールを有効にする</span>
              </label>
            </div>
          </div>

          {/* アクションボタン */}
          <div className="flex space-x-3 pt-6 mt-6 border-t border-gray-700">
            <button
              onClick={onClose}
              className="flex-1 px-4 py-2 bg-gray-600 hover:bg-gray-700 rounded-lg transition-colors"
              disabled={loading}
            >
              キャンセル
            </button>
            <button
              onClick={handleSave}
              className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors disabled:opacity-50"
              disabled={loading}
            >
              {loading ? '保存中...' : mode === 'create' ? '作成' : '更新'}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
