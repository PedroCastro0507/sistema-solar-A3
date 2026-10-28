"""Shader de iluminação difusa (Lambert) com luz pontual no Sol (origem da cena).

I = (ambiente + max(0, N . L)) * cor, em que L = normalize(posição_do_Sol - posição_do_fragmento)
e cor = textura(u, v) * cor_da_entidade (sem textura, o Panda3D usa uma textura branca e
fica só a cor sólida).
O lado voltado ao Sol fica iluminado e o oposto escurece (ciclo dia/noite com a rotação em Y).
"""
from ursina import Shader, Vec3

sombreamento_solar = Shader(
    language=Shader.GLSL,
    vertex='''#version 140
uniform mat4 p3d_ModelViewProjectionMatrix;
uniform mat4 p3d_ModelMatrix;
in vec4 p3d_Vertex;
in vec3 p3d_Normal;
in vec2 p3d_MultiTexCoord0;
out vec2 uv;
out vec3 mundo_pos;
out vec3 mundo_normal;
void main() {
    gl_Position = p3d_ModelViewProjectionMatrix * p3d_Vertex;
    mundo_pos = (p3d_ModelMatrix * p3d_Vertex).xyz;
    mundo_normal = mat3(p3d_ModelMatrix) * p3d_Normal;
    uv = p3d_MultiTexCoord0;
}''',
    fragment='''#version 140
uniform vec4 p3d_ColorScale;
uniform sampler2D p3d_Texture0;
uniform vec3 luz_pos;
uniform float ambiente;
in vec3 mundo_pos;
in vec3 mundo_normal;
in vec2 uv;
out vec4 fragColor;
void main() {
    vec3 N = normalize(mundo_normal);
    vec3 L = normalize(luz_pos - mundo_pos);
    float difusa = max(dot(N, L), 0.0);
    vec4 base = texture(p3d_Texture0, uv) * p3d_ColorScale;
    vec3 cor = base.rgb * (ambiente + (1.0 - ambiente) * difusa);
    fragColor = vec4(cor, base.a);
}''',
    default_input={'luz_pos': Vec3(0, 0, 0), 'ambiente': 0.05},
)
