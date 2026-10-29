import { mergeConfig } from 'vitest/config'
import base from '../../frontend/vite.config'

export default mergeConfig(base, {
  test: { include: ['tmp/770_frontend_scale_r29/770_request_state.test.ts'] },
})
