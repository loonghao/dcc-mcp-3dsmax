import maya.cmds as cmds

def import_fbx_file(fbx_path=None):
    """
    在 Maya 中导入 FBX 文件
    """
    if fbx_path is None:
        # 默认路径，与导出脚本匹配
        fbx_path = 'C:/temp/maya_balls_dynamics.fbx'
    
    # 检查文件是否存在
    import os
    if not os.path.exists(fbx_path):
        print(f'错误：文件不存在 - {fbx_path}')
        return {
            'status': 'error',
            'message': f'File not found: {fbx_path}'
        }
    
    # 导入 FBX 文件
    cmds.file(
        fbx_path,
        i=True,
        type='FBX',
        ignoreVersion=True,
        ra=True,
        mergeNamespacesOnClash=False,
        namespace=':'
    )
    
    print(f'成功导入 FBX 文件: {fbx_path}')
    
    # 获取导入的对象
    imported_nodes = cmds.ls(selection=False, type='transform')
    
    return {
        'status': 'success',
        'file_path': fbx_path,
        'imported_nodes': imported_nodes
    }

# 执行导入
if __name__ == '__main__':
    result = import_fbx_file()
    print('\n=== 导入结果 ===')
    for key, value in result.items():
        print(f'{key}: {value}')
