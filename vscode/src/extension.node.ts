// Sentry should be imported first
import { NodeSentryService } from './services/sentry/sentry.node'

import * as vscode from 'vscode'
import { NewViewProvider } from './newSidebar/NewViewProvider'

import { defaultAuthStatus } from '@sourcegraph/cody-shared'
import { startTokenReceiver } from './auth/token-receiver'
import { CommandsProvider } from './commands/services/provider'
import { BfgRetriever } from './completions/context/retrievers/bfg/bfg-retriever'
import { SourcegraphNodeCompletionsClient } from './completions/nodeClient'
import { getFullConfig } from './configuration'
import type { ExtensionApi } from './extension-api'
import { type ExtensionClient, defaultVSCodeExtensionClient } from './extension-client'
import { activate as activateCommon } from './extension.common'
import { initializeNetworkAgent, setCustomAgent } from './fetch.node'
import { isRunningInsideAgent } from './jsonrpc/isRunningInsideAgent'
import {
    type LocalEmbeddingsConfig,
    type LocalEmbeddingsController,
    createLocalEmbeddingsController,
} from './local-context/local-embeddings'
import { SymfRunner } from './local-context/symf'
import { authProvider } from './services/AuthProvider'
import { localStorage } from './services/LocalStorageProvider'
import { OpenTelemetryService } from './services/open-telemetry/OpenTelemetryService.node'
import { getExtensionDetails } from './services/telemetry-v2'
import { serializeConfigSnapshot } from './uninstall/serializeConfig'

/**
 * Activation entrypoint for the VS Code extension when running VS Code as a desktop app
 * (Node.js/Electron).
 */
export function activate(
    context: vscode.ExtensionContext,
    extensionClient?: ExtensionClient
): Promise<ExtensionApi> {
    console.log('Extension "Cody: AI Coding Assistant" is now active!')
    initializeNetworkAgent(context)

    // 当由 VSCode 激活时，只传递了扩展上下文。
    // 创建 VSCode 的默认客户端。
    extensionClient ||= defaultVSCodeExtensionClient()

    // 本地嵌入暂时只在 VSC 中支持。
    let isLocalEmbeddingsEnabled = !isRunningInsideAgent()

    // 可选的本地测试覆盖。
    isLocalEmbeddingsEnabled = vscode.workspace
        .getConfiguration()
        .get<boolean>('cody.experimental.localEmbeddings.enabled', isLocalEmbeddingsEnabled)

    const isSymfEnabled = vscode.workspace
        .getConfiguration()
        .get<boolean>('cody.experimental.symf.enabled', true)

    const isTelemetryEnabled = vscode.workspace
        .getConfiguration()
        .get<boolean>('cody.experimental.telemetry.enabled', true)

    const newViewProvider = new NewViewProvider();
    context.subscriptions.push(
        vscode.window.registerWebviewViewProvider(
            NewViewProvider.viewType, // 'newView'
            newViewProvider
        )
    );
    
    return activateCommon(context, {
        createLocalEmbeddingsController: isLocalEmbeddingsEnabled
            ? (config: LocalEmbeddingsConfig): Promise<LocalEmbeddingsController> =>
                  createLocalEmbeddingsController(context, config)
            : undefined,
        createCompletionsClient: (...args) => new SourcegraphNodeCompletionsClient(...args),
        createCommandsProvider: () => new CommandsProvider(),
        createSymfRunner: isSymfEnabled ? (...args) => new SymfRunner(...args) : undefined,
        createBfgRetriever: () => new BfgRetriever(context),
        createSentryService: (...args) => new NodeSentryService(...args),
        createOpenTelemetryService: isTelemetryEnabled
            ? (...args) => new OpenTelemetryService(...args)
            : undefined,
        startTokenReceiver: (...args) => startTokenReceiver(...args),
        onConfigurationChange: setCustomAgent,
        extensionClient,
    })
}

// 当 Cody 被停用时，我们将当前配置序列化到磁盘，
// 这样它可以与 Telemetry 一起发送，当 post-uninstall 脚本运行时。
// 在 post-uninstall 脚本中，vscode API 不可用。
export async function deactivate(): Promise<void> {
    const config = localStorage.getConfig() ?? (await getFullConfig())
    const authStatus = authProvider.instance?.getAuthStatus() ?? defaultAuthStatus
    const { anonymousUserID } = await localStorage.anonymousUserID()
    serializeConfigSnapshot({
        config,
        authStatus,
        anonymousUserID,
        extensionDetails: getExtensionDetails(config),
    })
}
