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
    <Card className="shadow-md border-gray-200">
      <CardHeader className="bg-gradient-to-r from-white to-gray-50 border-b border-gray-100">
        <CardTitle className="text-xl text-gray-800 flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-gradient-to-r from-blue-500 to-indigo-600"></div>
          服务器配置
        </CardTitle>
        <CardDescription className="text-gray-600">
          配置 Toolify Admin 服务器的基本运行参数
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6 p-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <div className="space-y-2">
            <Label htmlFor="host" className="font-medium text-gray-700 flex items-center gap-2">
              <span className="text-blue-500">🌐</span>
              监听地址
            </Label>
            <Input
              id="host"
              type="text"
              value={config.server.host}
              onChange={(e) => updateServer('host', e.target.value)}
              placeholder="0.0.0.0"
              className="border-gray-300 focus:border-blue-400 focus:ring-blue-500"
            />
            <p className="text-sm text-gray-500">
              服务器监听的 IP 地址
            </p>
          </div>

          <div className="space-y-2">
            <Label htmlFor="port" className="font-medium text-gray-700 flex items-center gap-2">
              <span className="text-green-500">🔌</span>
              监听端口
            </Label>
            <Input
              id="port"
              type="number"
              value={config.server.port}
              onChange={(e) => updateServer('port', parseInt(e.target.value))}
              placeholder="8000"
              min="1"
              max="65535"
              className="border-gray-300 focus:border-blue-400 focus:ring-blue-500"
            />
            <p className="text-sm text-gray-500">
              端口范围：1-65535
            </p>
          </div>

          <div className="space-y-2">
            <Label htmlFor="timeout" className="font-medium text-gray-700 flex items-center gap-2">
              <span className="text-orange-500">⏱️</span>
              请求超时（秒）
            </Label>
            <Input
              id="timeout"
              type="number"
              value={config.server.timeout}
              onChange={(e) => updateServer('timeout', parseInt(e.target.value))}
              placeholder="180"
              min="1"
              className="border-gray-300 focus:border-blue-400 focus:ring-blue-500"
            />
            <p className="text-sm text-gray-500">
              上游服务超时时间
            </p>
          </div>
        </div>

        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mt-6">
          <p className="text-sm text-blue-800">
            <span className="font-semibold">💡 提示：</span> 修改配置后，点击页面顶部的"保存配置"按钮即可实时生效，无需重启服务。
          </p>
        </div>
      </CardContent>
    </Card>
  )
}

