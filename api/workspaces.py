from api.schemas import TaskWorkspacePayload

from src.pipeline.tasks import TaskWorkspace


def workspace_to_payload(workspace: TaskWorkspace) -> TaskWorkspacePayload:
    return TaskWorkspacePayload(
        task_id=workspace.task_id,
        task_dir=workspace.task_dir,
        task_file_path=workspace.task_file_path,
        script_path=workspace.script_path,
        state_path=workspace.state_path,
        manifest_path=workspace.manifest_path,
        final_video_path=workspace.final_video_path,
        created_at=workspace.created_at,
        theme=workspace.theme,
        directories=workspace.directories(),
    )
