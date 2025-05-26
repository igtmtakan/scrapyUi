import React, { useState, useEffect } from 'react'
import { X } from 'lucide-react'
import { allTemplates, Template, CATEGORIES } from './templates'

interface TemplateSelectorProps {
  isOpen?: boolean
  onClose: () => void
  onSelectTemplate: (template: Template) => void
  inline?: boolean
}

export default function TemplateSelector({ isOpen = true, onClose, onSelectTemplate, inline = false }: TemplateSelectorProps) {
  const [selectedCategory, setSelectedCategory] = useState('all')
  const [searchTerm, setSearchTerm] = useState('')
  const [filteredTemplates, setFilteredTemplates] = useState<Template[]>(allTemplates)

  useEffect(() => {
    let filtered = allTemplates

    // カテゴリフィルタ
    if (selectedCategory !== 'all') {
      filtered = filtered.filter(template => template.category === selectedCategory)
    }

    // 検索フィルタ
    if (searchTerm) {
      filtered = filtered.filter(template =>
        template.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        template.description.toLowerCase().includes(searchTerm.toLowerCase())
      )
    }

    setFilteredTemplates(filtered)
  }, [selectedCategory, searchTerm])

  if (!isOpen && !inline) return null

  const containerClasses = inline
    ? "bg-gray-800 rounded-lg w-full flex flex-col"
    : "fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"

  const contentClasses = inline
    ? "w-full flex flex-col"
    : "bg-white dark:bg-gray-800 rounded-lg shadow-xl w-full max-w-6xl h-5/6 flex flex-col"

  return (
    <div className={containerClasses}>
      <div className={contentClasses}>
        {/* ヘッダー */}
        {!inline && (
          <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
              New Spider Template
            </h2>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
            >
              <X className="w-6 h-6" />
            </button>
          </div>
        )}

        {/* 検索とフィルタ */}
        <div className="p-6 border-b border-gray-200 dark:border-gray-700">
          <div className="flex flex-col sm:flex-row gap-4">
            {/* 検索バー */}
            <div className="flex-1">
              <input
                type="text"
                placeholder="Search templates..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              />
            </div>

            {/* カテゴリフィルタ */}
            <div className="sm:w-64">
              <select
                value={selectedCategory}
                onChange={(e) => setSelectedCategory(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              >
                {CATEGORIES.map(category => (
                  <option key={category.id} value={category.id}>
                    {category.name}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* 結果数表示 */}
          <div className="mt-4 text-sm text-gray-600 dark:text-gray-400">
            {filteredTemplates.length} template{filteredTemplates.length !== 1 ? 's' : ''} found
          </div>
        </div>

        {/* テンプレートグリッド */}
        <div className={`flex-1 overflow-y-auto p-6 ${inline ? 'max-h-96' : ''}`}>
          {filteredTemplates.length === 0 ? (
            <div className="text-center py-12">
              <p className="text-gray-500 dark:text-gray-400 text-lg">
                No templates found matching your criteria.
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {filteredTemplates.map(template => (
                <div
                  key={template.id}
                  onClick={() => onSelectTemplate(template)}
                  className="p-6 border border-gray-200 dark:border-gray-700 rounded-lg hover:border-blue-500 dark:hover:border-blue-400 cursor-pointer transition-all duration-200 group hover:shadow-lg bg-white dark:bg-gray-800"
                >
                  {/* アイコンとタイトル */}
                  <div className="flex items-center gap-3 mb-3">
                    <div className="text-blue-500 dark:text-blue-400 group-hover:text-blue-600 dark:group-hover:text-blue-300 transition-colors">
                      {template.icon}
                    </div>
                    <h3 className="font-semibold text-gray-900 dark:text-white group-hover:text-blue-600 dark:group-hover:text-blue-300 transition-colors">
                      {template.name}
                    </h3>
                  </div>

                  {/* 説明 */}
                  <p className="text-sm text-gray-600 dark:text-gray-400 mb-4 line-clamp-3">
                    {template.description}
                  </p>

                  {/* カテゴリバッジ */}
                  <div className="flex items-center justify-between">
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200">
                      {CATEGORIES.find(cat => cat.id === template.category)?.name || template.category}
                    </span>
                    <div className="text-xs text-gray-400 dark:text-gray-500 opacity-0 group-hover:opacity-100 transition-opacity">
                      Click to use
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* フッター */}
        {!inline && (
          <div className="p-6 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900">
            <div className="flex items-center justify-between">
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Select a template to get started with your spider
              </p>
              <button
                onClick={onClose}
                className="px-4 py-2 text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200 transition-colors"
              >
                Cancel
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
