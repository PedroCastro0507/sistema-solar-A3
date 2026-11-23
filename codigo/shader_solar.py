"""Shader de iluminação: Lambert com luz no Sol + sombras projetadas (eclipses).

1) Luz difusa de Lambert (Aula 7):
       I = ambiente + (1 - ambiente) . max(0, N . L) . visivel
   em que L = normalize(posição_do_Sol - posição_do_fragmento) e N . L é o produto escalar.

2) Sombras projetadas (eclipses): `visivel` é a fração do disco do Sol que o ponto
   enxerga. Para cada corpo que pode fazer sombra (o planeta e as luas do mesmo sistema,
   enviados em `ocl` como [centro, raio]) o shader mede, só com vetores:
       raio angular do Sol:    aS = asen(R_sol / d)  com o tamanho e a distância REAIS
                               (o Sol desenhado é ampliado só para ser visto; usar o
                               tamanho ampliado deixaria todas as sombras borradas)
       raio angular do corpo:  aO = asen(r / |C - P|)
       separação entre os dois: th = atan2(|u x s|, u . s)   (produto vetorial e escalar)
   em que u e s são as direções (normalizadas) do ponto P para o corpo e para o Sol.
   Se th >= aS + aO, o corpo não cobre o Sol (luz total). Se o corpo cobre o Sol
   inteiro, é sombra (umbra). Entre os dois, a cobertura varia suavemente (penumbra).
   Ex.: a sombra da Lua na Terra (eclipse solar), a Lua dentro da sombra da Terra
   (eclipse lunar), as sombras das luas em Júpiter e a sombra de Saturno nos anéis.

3) Sombra dos anéis em Saturno: o raio P + t.s (do ponto ao Sol) é cortado pelo plano
   dos anéis, n . (X - C) = 0  ->  t = n . (C - P) / (n . s). Se o ponto de corte X
   fica entre o raio interno e o externo, a luz passa pela textura do anel (alfa).

cor final = textura(u, v) * cor_da_entidade * I.
"""
from panda3d.core import PTA_LVecBase4f
from ursina import Shader, Vec2, Vec3, load_texture

MAX_OCL = 8          # máximo de corpos que fazem sombra em um mesmo corpo

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
uniform vec3 luz_pos;          // centro do Sol
uniform float ang_sol;         // raio angular REAL do Sol visto deste corpo (rad)
uniform float ambiente;
uniform float lambert;         // 1 = esfera (N.L); 0 = anel (fino, sem N.L)
uniform float n_ocl;         // quantos corpos em ocl[] valem
uniform vec4 ocl[8];           // corpos que fazem sombra: xyz = centro, w = raio
uniform float anel_on;         // 1 só em Saturno: sombra dos anéis
uniform vec3 anel_c;
uniform vec3 anel_n;
uniform vec2 anel_r;           // raio interno e externo dos anéis
uniform sampler2D anel_tex;
in vec3 mundo_pos;
in vec3 mundo_normal;
in vec2 uv;
out vec4 fragColor;

float visivel(vec3 P) {
    vec3 paraSol = luz_pos - P;
    float dS = length(paraSol);
    vec3 s = paraSol / dS;
    float aS = ang_sol;
    float vis = 1.0;
    for (int i = 0; i < 8; i++) {
        if (float(i) >= n_ocl) break;
        vec3 paraC = ocl[i].xyz - P;
        float dC = length(paraC);
        float r = ocl[i].w;
        if (dC <= r * 1.0001 || dC >= dS) continue;      // dentro do corpo ou atrás do Sol
        vec3 u = paraC / dC;
        if (dot(u, s) <= 0.0) continue;                  // corpo do lado oposto ao Sol
        float aO = asin(min(r / dC, 1.0));
        float th = atan(length(cross(u, s)), dot(u, s)); // ângulo entre corpo e Sol
        float total = min(1.0, (aO * aO) / (aS * aS));   // fração máxima do Sol coberta
        float cob;
        if (th >= aS + aO) cob = 0.0;
        else if (th <= abs(aS - aO)) cob = total;
        else cob = total * smoothstep(0.0, 1.0, (aS + aO - th) / (aS + aO - abs(aS - aO)));
        vis *= 1.0 - cob;
    }
    if (anel_on > 0.5) {
        float ns = dot(anel_n, s);
        if (abs(ns) > 1e-6) {
            float t = dot(anel_n, anel_c - P) / ns;
            if (t > 0.0) {
                float rr = length(P + s * t - anel_c);
                if (rr > anel_r.x && rr < anel_r.y) {
                    float a = texture(anel_tex, vec2((rr - anel_r.x) / (anel_r.y - anel_r.x), 0.5)).a;
                    vis *= 1.0 - 0.85 * a;
                }
            }
        }
    }
    return vis;
}

void main() {
    vec3 N = normalize(mundo_normal);
    vec3 L = normalize(luz_pos - mundo_pos);
    float difusa = mix(1.0, max(dot(N, L), 0.0), lambert);
    if (difusa > 0.0) difusa *= visivel(mundo_pos);
    vec4 base = texture(p3d_Texture0, uv) * p3d_ColorScale;
    vec3 cor = base.rgb * (ambiente + (1.0 - ambiente) * difusa);
    fragColor = vec4(cor, base.a);
}''',
    default_input={
        'luz_pos': Vec3(0, 0, 0), 'ang_sol': 0.005, 'ambiente': 0.05, 'lambert': 1.0,
        'n_ocl': 0.0, 'ocl': lambda: PTA_LVecBase4f.emptyArray(MAX_OCL),
        'anel_on': 0.0, 'anel_c': Vec3(0, 0, 0), 'anel_n': Vec3(0, 1, 0), 'anel_r': Vec2(1.0, 2.0),
        'anel_tex': lambda: load_texture('white_cube'),
    },
)
