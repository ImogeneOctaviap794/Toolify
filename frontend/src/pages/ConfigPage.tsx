import { useEffect, useState } from 'react'
import { useConfigStore, useAuthStore } from '@/lib/store'
import { adminApi } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import ServerConfig from '@/components/ServerConfig'
import UpstreamServices from '@/components/UpstreamServices'
import ClientAuth from '@/components/ClientAuth'
import Features from '@/components/Features'
import { AlertCircle, CheckCircle2, LogOut, Save, RefreshCw } from 'lucide-react'

export default function ConfigPage() {
  const { config, isLoading, error, setConfig, setLoading, setError } = useConfigStore()
  const logout = useAuthStore((state) => state.logout)
  const [activeTab, setActiveTab] = useState('server')
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
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b shadow-sm sticky top-0 z-10">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Toolify Admin 配置管理</h1>
              <p className="text-sm text-muted-foreground mt-1">
                可视化管理 Toolify 服务的所有配置选项
              </p>
            </div>
            <div className="flex items-center gap-3">
              <Button onClick={handleSave} disabled={isSaving} size="lg">
                <Save className="w-4 h-4 mr-2" />
                {isSaving ? '保存中...' : '保存配置'}
              </Button>
              <Button variant="outline" onClick={handleLogout} size="lg">
                <LogOut className="w-4 h-4 mr-2" />
                退出登录
              </Button>
            </div>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8">
        {saveSuccess && (
          <Alert variant="success" className="mb-6">
            <CheckCircle2 className="h-4 w-4" />
            <AlertTitle>保存成功</AlertTitle>
            <AlertDescription>
              配置已更新并已实时生效。
            </AlertDescription>
          </Alert>
        )}

        {error && (
          <Alert variant="destructive" className="mb-6">
            <AlertCircle className="h-4 w-4" />
            <AlertTitle>错误</AlertTitle>
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="grid w-full grid-cols-4 mb-6">
            <TabsTrigger value="server">服务器配置</TabsTrigger>
            <TabsTrigger value="upstream">上游服务</TabsTrigger>
            <TabsTrigger value="client">客户端认证</TabsTrigger>
            <TabsTrigger value="features">功能配置</TabsTrigger>
          </TabsList>

          <TabsContent value="server">
            <ServerConfig config={config} setConfig={setConfig} />
          </TabsContent>

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

