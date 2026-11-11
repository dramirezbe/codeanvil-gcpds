import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import App from './App'

vi.mock('./ProjectWorkflows', () => ({ ProjectWorkflows: () => <div>Project workflows</div> }))
vi.mock('./Workspace', () => ({ Workspace: ({ project, active }: { project: { name: string }; active: string }) =>
  <h1>{project.name} · {active}</h1> }))
vi.mock('./ActionsPanel', () => ({ ActionsPanel: ({ projectPath }: { projectPath?: string }) =>
  <h1>{projectPath ? 'Project CLI actions' : 'Global CLI actions'}</h1> }))

const project = { id: 'sample', name: 'Sample project', path: '/home/alice/Documents/sample' }
const localUser = { name: 'alice', home: '/home/alice' }

function bootstrap(projects = [project], user = localUser, startupProject: typeof project | null = null) {
  vi.stubGlobal('fetch', vi.fn().mockImplementation(async () => new Response(JSON.stringify({
    mode: startupProject ? 'workspace' : 'launcher', project: startupProject, projects, user,
  }), { headers: { 'Content-Type': 'application/json' } })))
}

describe('Launcher navigation', () => {
  it('shows only global actions until a project opens, and returns from both CLI and workspace', async () => {
    const user = userEvent.setup()
    bootstrap()
    render(<App />)
    expect(await screen.findByRole('heading', { name: 'Projects in CodeAnvil' })).toBeInTheDocument()
    const navigation = screen.getByRole('navigation', { name: 'Workspace navigation' })
    expect(within(navigation).getAllByRole('button').map(button => button.textContent)).toEqual(['CLI actions'])

    await user.click(within(navigation).getByRole('button', { name: 'CLI actions' }))
    expect(screen.getByRole('heading', { name: 'Global CLI actions' })).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Project launcher' }))
    expect(screen.getByRole('heading', { name: 'Projects in CodeAnvil' })).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: /Sample project/ }))
    expect(screen.getByRole('heading', { name: 'Sample project · Overview' })).toBeInTheDocument()
    expect(within(navigation).getByRole('button', { name: 'Reports' })).toBeInTheDocument()
    await user.click(within(navigation).getByRole('button', { name: 'CLI actions' }))
    expect(screen.getByRole('heading', { name: 'Project CLI actions' })).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Project launcher' }))
    expect(screen.getByRole('heading', { name: 'Projects in CodeAnvil' })).toBeInTheDocument()
    expect(within(navigation).getAllByRole('button')).toHaveLength(1)
  })

  it('can return to the launcher when the server initially detects a project', async () => {
    const user = userEvent.setup()
    bootstrap([project], localUser, project)
    render(<App />)
    expect(await screen.findByRole('heading', { name: 'Sample project · Overview' })).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Project launcher' }))
    expect(await screen.findByRole('heading', { name: 'Projects in CodeAnvil' })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Reports' })).not.toBeInTheDocument()
  })
})

describe('Recent project paths', () => {
  it('shows user/home context and abbreviates only directories inside that home', async () => {
    const outside = { id: 'outside', name: 'Outside project', path: '/home/alice-other/sample' }
    bootstrap([project, outside, { id: 'home', name: 'Home project', path: localUser.home }])
    render(<App />)
    const context = await screen.findByLabelText('Local user and home')
    expect(context).toHaveTextContent('alice')
    expect(context).toHaveTextContent('/home/alice')
    expect(screen.getByText('~/Documents/sample')).toHaveAttribute('title', project.path)
    expect(screen.getByText(outside.path)).toHaveAttribute('title', outside.path)
    expect(screen.getByText('~')).toHaveAttribute('title', localUser.home)
  })

  it('recognizes Windows home boundaries and drive case without altering full paths', async () => {
    const home = 'C:\\Users\\Alice'
    const inside = { id: 'inside', name: 'Windows project', path: 'c:\\users\\alice\\Documents\\sample' }
    const outside = { id: 'outside', name: 'Other user', path: 'C:\\Users\\Alice-Other\\sample' }
    bootstrap([inside, outside], { name: 'Alice', home })
    render(<App />)
    expect(await screen.findByText('~/Documents/sample')).toHaveAttribute('title', inside.path)
    expect(screen.getByText(outside.path)).toHaveAttribute('title', outside.path)
  })
})
