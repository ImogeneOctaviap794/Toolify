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
    <Card>
      <CardHeader>
        <CardTitle>客户端认证配置</CardTitle>
        <CardDescription>
          管理允许访问 Toolify Admin 服务的客户端 API 密钥
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-3">
          {config.client_authentication.allowed_keys.map((key, index) => (
            <div key={index} className="flex items-center gap-2">
              <div className="flex-1 space-y-2">
                <Label htmlFor={`key-${index}`}>API Key {index + 1}</Label>
                <Input
                  id={`key-${index}`}
                  type="text"
                  value={key}
                  onChange={(e) => updateKey(index, e.target.value)}
                  placeholder="sk-your-api-key-here"
                />
              </div>
              {config.client_authentication.allowed_keys.length > 1 && (
                <Button
                  variant="destructive"
                  size="icon"
                  onClick={() => removeKey(index)}
                  className="mt-8"
                >
                  <Trash2 className="w-4 h-4" />
                </Button>
              )}
            </div>
          ))}
        </div>

        <Button onClick={addKey} variant="outline" className="w-full">
          <Plus className="w-4 h-4 mr-2" />
          添加 API Key
        </Button>

        <div className="bg-muted/50 border rounded-lg p-4 mt-6">
          <h4 className="font-medium mb-2">使用说明</h4>
          <ul className="text-sm text-muted-foreground space-y-1 list-disc list-inside">
            <li>这些 API Key 用于客户端访问 Toolify 服务时的身份验证</li>
            <li>请妥善保管这些密钥，不要泄露给未授权的用户</li>
            <li>建议使用长度至少 32 位的随机字符串作为 API Key</li>
            <li>客户端需要在请求头中携带：Authorization: Bearer YOUR_API_KEY</li>
          </ul>
        </div>
      </CardContent>
    </Card>
  )
}

