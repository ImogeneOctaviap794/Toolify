import { useEffect, useState } from 'react'
import { useConfigStore, useAuthStore } from '@/lib/store'
import { adminApi } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import UpstreamServices from '@/components/UpstreamServices'
import ClientAuth from '@/components/ClientAuth'
import Features from '@/components/Features'
import { AlertCircle, CheckCircle2, LogOut, Save, RefreshCw } from 'lucide-react'

export default function ConfigPage() {
  const { config, isLoading, error, setConfig, setLoading, setError } = useConfigStore()
  const logout = useAuthStore((state) => state.logout)
  const [activeTab, setActiveTab] = useState('upstream')
  const [saveSuccess, setSaveSuccess] = useState(false)
  const [isSaving, setIsSaving] = useState(false)

  useEffect(() => {
    loadConfig()
  }, [])

  const loadConfig = async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await adminApi.getConfig()
      setConfig(data)
    } catch (err: any) {
      setError(err.response?.data?.detail || '加载配置失败')
    } finally {
      setLoading(false)
    }
  }

  const handleSave = async () => {
    if (!config) return

    setIsSaving(true)
    setSaveSuccess(false)
    setError(null)

    try {
      await adminApi.updateConfig(config)
      setSaveSuccess(true)
      setTimeout(() => setSaveSuccess(false), 5000)
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || '保存配置失败'
      setError(errorMsg)
    } finally {
      setIsSaving(false)
    }
  }

  const handleLogout = () => {
    logout()
    window.location.href = '/admin/'
  }

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <RefreshCw className="w-8 h-8 animate-spin mx-auto mb-4 text-primary" />
          <p className="text-muted-foreground">加载配置中...</p>
        </div>
      </div>
    )
  }

  if (!config) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <Alert variant="destructive" className="max-w-md">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>加载失败</AlertTitle>
          <AlertDescription>{error || '无法加载配置'}</AlertDescription>
        </Alert>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-50 via-gray-50 to-gray-100">
      <header className="bg-white/80 backdrop-blur-md border-b border-gray-200/50 shadow-sm sticky top-0 z-50">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-lg flex items-center justify-center shadow-lg">
                <span className="text-white font-bold text-lg">T</span>
              </div>
              <div>
                <h1 className="text-2xl font-bold bg-gradient-to-r from-gray-900 to-gray-700 bg-clip-text text-transparent">
                  Toolify-code
                </h1>
                <p className="text-sm text-gray-500">
                  智能服务配置管理平台
                </p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <Button 
                onClick={handleSave} 
                disabled={isSaving} 
                size="lg"
                className="bg-gradient-to-r from-blue-500 to-indigo-600 hover:from-blue-600 hover:to-indigo-700 text-white shadow-md transition-all hover:shadow-lg"
              >
                <Save className="w-4 h-4 mr-2" />
                {isSaving ? '保存中...' : '保存配置'}
              </Button>
              <Button 
                variant="outline" 
                onClick={handleLogout} 
                size="lg"
                className="hover:bg-gray-50 transition-colors"
              >
                <LogOut className="w-4 h-4 mr-2" />
                退出登录
              </Button>
            </div>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-6 py-8">
        {saveSuccess && (
          <Alert className="mb-6 bg-green-50 border-green-200 text-green-800">
            <CheckCircle2 className="h-4 w-4 text-green-600" />
            <AlertTitle className="text-green-800">保存成功</AlertTitle>
            <AlertDescription className="text-green-700">
              配置已更新并已实时生效，无需重启服务。
            </AlertDescription>
          </Alert>
        )}

        {error && (
          <Alert variant="destructive" className="mb-6 shadow-sm">
            <AlertCircle className="h-4 w-4" />
            <AlertTitle>错误</AlertTitle>
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <TabsList className="grid w-full grid-cols-3 h-12 bg-white shadow-sm border border-gray-200">
            <TabsTrigger value="upstream" className="data-[state=active]:bg-gradient-to-r data-[state=active]:from-blue-500 data-[state=active]:to-indigo-600 data-[state=active]:text-white data-[state=active]:shadow-sm">
              <span className="font-medium">🔗 上游服务</span>
            </TabsTrigger>
            <TabsTrigger value="client" className="data-[state=active]:bg-gradient-to-r data-[state=active]:from-blue-500 data-[state=active]:to-indigo-600 data-[state=active]:text-white data-[state=active]:shadow-sm">
              <span className="font-medium">🔐 认证</span>
            </TabsTrigger>
            <TabsTrigger value="features" className="data-[state=active]:bg-gradient-to-r data-[state=active]:from-blue-500 data-[state=active]:to-indigo-600 data-[state=active]:text-white data-[state=active]:shadow-sm">
              <span className="font-medium">⚙️ 功能</span>
            </TabsTrigger>
          </TabsList>

          <TabsContent value="upstream">
            <UpstreamServices config={config} setConfig={setConfig} />
          </TabsContent>

          <TabsContent value="client">
            <ClientAuth config={config} setConfig={setConfig} />
          </TabsContent>

          <TabsContent value="features">
            <Features config={config} setConfig={setConfig} />
          </TabsContent>
        </Tabs>
      </main>
    </div>
  )
}

