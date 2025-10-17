import { ConfigData } from '@/lib/api'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card'
import { Input } from './ui/input'
import { Label } from './ui/label'
import { Button } from './ui/button'
import { Plus, Trash2 } from 'lucide-react'

interface ClientAuthProps {
  config: ConfigData
  setConfig: (config: ConfigData) => void
}

export default function ClientAuth({ config, setConfig }: ClientAuthProps) {
  const addKey = () => {
    const newKeys = [...config.client_authentication.allowed_keys, '']
    setConfig({
      ...config,
      client_authentication: {
        ...config.client_authentication,
        allowed_keys: newKeys
      }
    })
  }

  const removeKey = (index: number) => {
    const newKeys = config.client_authentication.allowed_keys.filter((_, i) => i !== index)
    setConfig({
      ...config,
      client_authentication: {
        ...config.client_authentication,
        allowed_keys: newKeys
      }
    })
  }

  const updateKey = (index: number, value: string) => {
    const newKeys = [...config.client_authentication.allowed_keys]
    newKeys[index] = value
    setConfig({
      ...config,
      client_authentication: {
        ...config.client_authentication,
        allowed_keys: newKeys
      }
    })
  }

  return (
    <Card className="shadow-md border-gray-200">
      <CardHeader className="bg-gradient-to-r from-white to-gray-50 border-b border-gray-100">
        <CardTitle className="text-xl text-gray-800 flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-gradient-to-r from-blue-500 to-indigo-600"></div>
          客户端认证配置
        </CardTitle>
        <CardDescription className="text-gray-600">
          管理允许访问 Toolify Admin 服务的客户端 API 密钥
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6 p-6">
        <div className="space-y-4">
          {config.client_authentication.allowed_keys.map((key, index) => (
            <div key={index} className="flex items-center gap-3 p-4 rounded-lg bg-gradient-to-r from-gray-50 to-gray-100 border border-gray-200">
              <div className="flex-1 space-y-2">
                <Label htmlFor={`key-${index}`} className="font-medium text-gray-700 flex items-center gap-2">
                  <span className="text-yellow-500">🔑</span>
                  API Key {index + 1}
                </Label>
                <Input
                  id={`key-${index}`}
                  type="text"
                  value={key}
                  onChange={(e) => updateKey(index, e.target.value)}
                  placeholder="sk-your-api-key-here"
                  className="font-mono text-sm border-gray-300 focus:border-blue-400 focus:ring-blue-500"
                />
              </div>
              {config.client_authentication.allowed_keys.length > 1 && (
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => removeKey(index)}
                  className="hover:bg-red-50 hover:text-red-600 transition-colors mt-7"
                >
                  <Trash2 className="w-4 h-4" />
                </Button>
              )}
            </div>
          ))}
        </div>

        <Button 
          onClick={addKey} 
          className="w-full bg-gradient-to-r from-green-500 to-green-600 hover:from-green-600 hover:to-green-700 text-white shadow-sm hover:shadow-md transition-all"
        >
          <Plus className="w-4 h-4 mr-2" />
          添加新的 API Key
        </Button>

        <div className="bg-gradient-to-br from-blue-50 to-indigo-50 border border-blue-200 rounded-lg p-5 mt-6">
          <h4 className="font-semibold text-gray-800 mb-3 flex items-center gap-2">
            <span className="text-blue-500">📋</span>
            使用说明
          </h4>
          <div className="space-y-2">
            <div className="flex items-start gap-2">
              <span className="text-green-500 mt-0.5">✓</span>
              <p className="text-sm text-gray-600">这些 API Key 用于客户端访问 Toolify 服务时的身份验证</p>
            </div>
            <div className="flex items-start gap-2">
              <span className="text-orange-500 mt-0.5">⚠️</span>
              <p className="text-sm text-gray-600">请妥善保管这些密钥，不要泄露给未授权的用户</p>
            </div>
            <div className="flex items-start gap-2">
              <span className="text-blue-500 mt-0.5">💡</span>
              <p className="text-sm text-gray-600">建议使用长度至少 32 位的随机字符串作为 API Key</p>
            </div>
            <div className="flex items-start gap-2">
              <span className="text-purple-500 mt-0.5">📡</span>
              <p className="text-sm text-gray-600 font-mono bg-white px-2 py-1 rounded border border-gray-200 inline-block">
                Authorization: Bearer YOUR_API_KEY
              </p>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

