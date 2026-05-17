"""
在 Maya 2026 中创建随机小球并导出 FBX
功能：
1. 创建 10 个随机位置、随机颜色的小球
2. 添加刚体动力学（主动刚体 + 重力）
3. 创建地面（被动刚体）
4. 烘焙动力学动画
5. 导出为 FBX 文件
"""

import maya.cmds as cmds
import maya.mel as mel
import random
import os

def create_balls_with_dynamics():
    """
    创建 10 个随机位置、随机颜色、带动力学的小球
    并导出 FBX 文件
    """
    print("=" * 60)
    print("开始创建带动力学的小球...")
    print("=" * 60)
    
    # 清除场景中的所有物体
    cmds.file(new=True, force=True)
    
    # 创建地面作为被动刚体
    print("\n[1/6] 创建地面...")
    ground = cmds.polyPlane(name='ground', width=20, height=20)[0]
    cmds.setAttr(ground + '.translateY', -2)
    
    # 使地面成为被动刚体
    cmds.select(ground)
    cmds.rigidBody(passive=True, bounciness=0.5)
    print(f"  ✓ 已创建地面: {ground}")
    
    # 创建 10 个随机小球
    print("\n[2/6] 创建 10 个随机小球...")
    balls = []
    materials = []
    
    for i in range(10):
        # 随机位置
        pos_x = random.uniform(-5, 5)
        pos_y = random.uniform(5, 15)
        pos_z = random.uniform(-5, 5)
        
        # 创建球体
        ball_name = f'ball_{i+1}'
        ball = cmds.polySphere(name=ball_name, radius=0.5)[0]
        balls.append(ball)
        
        # 设置随机位置
        cmds.setAttr(ball + '.translateX', pos_x)
        cmds.setAttr(ball + '.translateY', pos_y)
        cmds.setAttr(ball + '.translateZ', pos_z)
        
        # 创建随机颜色材质
        mat_name = f'ball_mat_{i+1}'
        shader = cmds.shadingNode('lambert', asShader=True, name=mat_name)
        materials.append(shader)
        
        # 随机颜色
        r = random.uniform(0, 1)
        g = random.uniform(0, 1)
        b = random.uniform(0, 1)
        cmds.setAttr(shader + '.color', r, g, b)
        
        # 创建 shading group 并连接
        sg_name = f'{mat_name}_SG'
        sg = cmds.sets(renderable=True, noSurfaceShader=True, empty=True, name=sg_name)
        cmds.connectAttr(shader + '.outColor', sg + '.surfaceShader', force=True)
        
        # 将材质赋给球体
        cmds.select(ball)
        cmds.sets(edit=True, forceElement=sg)
        
        # 添加主动刚体（动力学）
        cmds.select(ball)
        cmds.rigidBody(active=True, bounciness=0.7, mass=1.0)
        
        print(f"  ✓ 球 {i+1}: {ball} at ({pos_x:.2f}, {pos_y:.2f}, {pos_z:.2f}), color=({r:.2f}, {g:.2f}, {b:.2f})")
    
    # 添加重力场
    print("\n[3/6] 添加重力场...")
    cmds.select(balls)
    gravity = cmds.gravity(name='gravityField', magnitude=9.8)[0]
    print(f"  ✓ 已添加重力场: {gravity}")
    
    # 设置动画时间范围
    print("\n[4/6] 设置动画时间范围...")
    cmds.playbackOptions(minTime=1, maxTime=200)
    # Maya 2026 兼容性：使用 MEL 设置当前时间
    mel.eval('currentTime 1;')
    print("  ✓ 时间范围设置为 1-200 帧，当前时间设置为第 1 帧")
    
    # 烘焙动力学动画
    print("\n[5/6] 烘焙动力学动画（这可能需要一些时间）...")
    try:
        # 选择所有小球
        cmds.select(balls)
        
        # 使用 Maya 的烘焙模拟功能
        # 这会将动力学模拟转换为关键帧动画
        mel.eval('source "artBakeAnim.mel";')
        mel.eval('artBakeAnimOverrideAll;')
        
        print("  ✓ 动力学动画已烘焙为关键帧")
    except Exception as e:
        print(f"  ⚠ 烘焙警告: {e}")
        print("  → 将继续导出，FBX 可能不包含动画")
    
    # 导出 FBX 文件
    print("\n[6/6] 导出 FBX 文件...")
    output_path = 'C:/temp/maya_balls_dynamics.fbx'
    
    # 确保目录存在
    output_dir = os.path.dirname(output_path)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"  ✓ 已创建目录: {output_dir}")
    
    # 选择所有小球和地面
    cmds.select(balls + [ground])
    
    # 导出选中对象为 FBX
    # FBX 导出选项说明：
    # -v=0: 详细程度（0=无输出）
    # -a: 导出动画
    # -s: 导出平滑网格
    try:
        # 先尝试使用 FBX Export 插件
        if not cmds.pluginInfo('fbxmaya', query=True, loaded=True):
            cmds.loadPlugin('fbxmaya')
            print("  ✓ 已加载 FBX Maya 插件")
        
        # 导出 FBX
        cmds.file(
            output_path,
            force=True,
            options='v=0;',
            type='FBX export',
            exportSelected=True
        )
        print(f"  ✓ 已导出 FBX 文件到: {output_path}")
        export_success = True
    except Exception as e:
        print(f"  ✗ FBX 导出失败: {e}")
        export_success = False
    
    # 输出成功信息
    print("\n" + "=" * 60)
    print("完成！")
    print("=" * 60)
    print(f"成功创建 {len(balls)} 个带动力学的小球")
    print(f"小球列表: {balls}")
    if export_success:
        print(f"FBX 文件: {output_path}")
    print("=" * 60)
    
    return {
        'balls_created': len(balls),
        'ball_names': balls,
        'materials': materials,
        'fbx_path': output_path if export_success else None,
        'status': 'success' if export_success else 'partial_success'
    }

def run_in_maya():
    """
    在 Maya 中运行的主函数
    可以通过 Maya 的 Script Editor 或命令行调用
    """
    try:
        result = create_balls_with_dynamics()
        return result
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
        return {'status': 'error', 'message': str(e)}

# 执行函数
if __name__ == '__main__':
    result = run_in_maya()
    print('\n=== 执行结果 ===')
    for key, value in result.items():
        print(f'{key}: {value}')
