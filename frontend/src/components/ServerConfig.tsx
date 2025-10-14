import { ConfigData } from '@/lib/api'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card'
import { Input } from './ui/input'
import { Label } from './ui/label'

interface ServerConfigProps {
  config: ConfigData
  setConfig: (config: ConfigData) => void
}

export default function ServerConfig({ config, setConfig }: ServerConfigProps) {
  const updateServer = (field: keyof ConfigData['server'], value: string | number) => {
    setConfig({
      ...config,
      server: {
        ...config.server,
        [field]: value
      }
    })
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>服务器配置</CardTitle>
        <CardDescription>
          配置 Toolify Admin 服务器的基本运行参数
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="space-y-2">
            <Label htmlFor="host">监听地址</Label>
            <Input
              id="host"
              type="text"
              value={config.server.host}
              onChange={(e) => updateServer('host', e.target.value)}
              placeholder="0.0.0.0"
            />
            <p className="text-sm text-muted-foreground">
              服务器监听的 IP 地址，0.0.0.0 表示监听所有网络接口
            </p>
          </div>

          <div className="space-y-2">
            <Label htmlFor="port">监听端口</Label>
            <Input
              id="port"
              type="number"
              value={config.server.port}
              onChange={(e) => updateServer('port', parseInt(e.target.value))}
              placeholder="8000"
              min="1"
              max="65535"
            />
            <p className="text-sm text-muted-foreground">
              服务器监听的端口号（1-65535）
            </p>
          </div>

          <div className="space-y-2">
            <Label htmlFor="timeout">请求超时（秒）</Label>
            <Input
              id="timeout"
              type="number"
              value={config.server.timeout}
              onChange={(e) => updateServer('timeout', parseInt(e.target.value))}
              placeholder="180"
              min="1"
            />
            <p className="text-sm text-muted-foreground">
              上游服务请求的超时时间
            </p>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

