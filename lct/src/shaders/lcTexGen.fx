#define NumberOfMipMaps 0
#define PI 3.1415926
#define GammaCorrection 2.2

//------------------------------------
// Per Frame parameters
//------------------------------------
cbuffer UpdatePerFrame : register(b0)
{
    float4x4 worldInvXpose  : WorldInverseTranspose < string UIWidget = "None"; >;
    float4x4 viewInv        : ViewInverse           < string UIWidget = "None"; >;
    float4x4 view           : View                  < string UIWidget = "None"; >;
    float4x4 prj            : Projection            < string UIWidget = "None"; >;
    float4x4 viewPrj        : ViewProjection        < string UIWidget = "None"; >;
    float4x4 worldViewPrj   : WorldViewProjection   < string UIWidget = "None"; >;
    float4x4 world          : World                 < string UIWidget = "None"; >;

    // A shader may wish to do different actions when Maya is rendering the preview swatch (e.g. disable displacement)
    // This value will be true if Maya is rendering the swatch
    bool IsSwatchRender     : MayaSwatchRender      < string UIWidget = "None"; > = false;

    // If the user enables viewport gamma correction in Maya's global viewport rendering settings, the shader should not do gamma again
    bool MayaFullScreenGamma : MayaGammaCorrection < string UIWidget = "None"; > = false;
}

//------------------------------------
// Samplers
//------------------------------------
SamplerState CubeMapSampler
{
    Filter = ANISOTROPIC;
    AddressU = Clamp;
    AddressV = Clamp;
    AddressW = Clamp;
};

SamplerState SamplerAnisoWrap
{
    Filter = ANISOTROPIC;
    AddressU = Wrap;
    AddressV = Wrap;
};

//------------------------------------
// Textures
//------------------------------------

Texture2D LitSphereTexture
<
    string UIGroup = "Textures";
    string ResourceName = "";
    string UIWidget = "FilePicker";
    string UIName = "Lit Sphere Texture";
    string ResourceType = "2D";
    int mipmaplevels = NumberOfMipMaps;
    int UIOrder = 101;
    int UVEditorOrder = 1;
>;

Texture2D TilingSphereTexture
<
    string UIGroup = "Textures";
    string ResourceName = "";
    string UIWidget = "FilePicker";
    string UIName = "Tiling Texture";
    string ResourceType = "2D";
    int mipmaplevels = NumberOfMipMaps;
    int UIOrder = 101;
    int UVEditorOrder = 1;
>;

Texture2D NormalTexture
<
    string UIGroup = "Textures";
    string ResourceName = "";
    string UIWidget = "FilePicker";
    string UIName = "Normals";
    string ResourceType = "2D";
    int mipmaplevels = NumberOfMipMaps;
    int UIOrder = 102;
    int UVEditorOrder = 2;
>;

TextureCube MaskCube : environment
<
    string ResourceName = "";
    string UIWidget = "FilePicker";
    string UIName = "Cube Mask";    // Note: do not rename to 'Reflection Cube Map'. This is named this way for backward compatibilty (resave after compat_maya_2013ff10.mel)
    string ResourceType = "Cube";
    int mipmaplevels = 0; // Use (or load) max number of mip map levels so we can use blurring
    int UIOrder = 1001;
    int UVEditorOrder = 5;
    int SasUiVisible = 0; // hide from maya ui, also must not have ui group
>;

//------------------------------------
// Per Object parameters
//------------------------------------
cbuffer UpdatePerObject : register(b1)
{
    bool OutputUvSpace
    <
        string UIGroup = "Global Properties";
        string UIName = "Output in UV space";
        int UIOrder = 200;
    > = false;

    bool OutputLuminanceOnly
    <
        string UIGroup = "Global Properties";
        string UIName = "Render in Greyscale";
        int UIOrder = 201;
    > = false;

    bool UseNormalTexture
    <
        string UIGroup = "Global Properties";
        string UIName = "Normal Map";
        int UIOrder = 202;
    > = true;

    bool useLitSphereLighten
    <
        string UIGroup = "LitSphere Properties";
        string UIName = "Use Lighten Blend";
        int UIOrder = 301;
    > = false;

    bool useLitSphereBlend
    <
        string UIGroup = "LitSphere Properties";
        string UIName = "Use Projection Blend";
        int UIOrder = 302;
    > = false;

    bool useLitSphereCube
    <
        string UIGroup = "LitSphere Properties";
        string UIName = "Use Cubemap Blend";
        int UIOrder = 302;
    > = false;

    bool LitSphereFlipX
    <
        string UIGroup = "LitSphere Properties";
        string UIName = "Flip Lit Sphere X";
        int UIOrder = 303;
    > = false;

    bool LitSphereFlipY
    <
        string UIGroup = "LitSphere Properties";
        string UIName = "Flip Lit Sphere Y";
        int UIOrder = 304;
    > = false;


    float rotateYaw
    <
        string UIGroup = "LitSphere Properties";
        string UIWidget = "Slider";
        float UIMin = -360.0;
        float UIMax = 360.0;
        float UIStep = 0.001;
        string UIName = "Rotate Projection";
        int UIOrder = 305;
    > = 0.0;


    float projectionBlend
    <
        string UIGroup = "LitSphere Properties";
        string UIWidget = "Slider";
        float UIMin = 0.0;
        float UIMax = 1.0;
        float UIStep = 0.001;
        string UIName = "Projection Blur";
        int UIOrder = 306;
    > = 0.0;

    float textureScale
    <
        string UIGroup = "TriPlanar Properties";
        string UIWidget = "Slider";
        float UIMin = 0.0;
        float UIMax = 10.0;
        float UIStep = 0.001;
        string UIName = "TriPlanar Scale";
        int UIOrder = 505;
    > = 0.5;

    float triBlend
    <
        string UIGroup = "TriPlanar Properties";
        string UIWidget = "Slider";
        float UIMin = 0.0;
        float UIMax = 1.0;
        float UIStep = 0.0001;
        string UIName = "TriPlanar Blend";
        int UIOrder = 505;
    > = 0.0;

} //end UpdatePerObject cbuffer


//------------------------------------
// Functions
//------------------------------------

float invert(float input)
{
    return (1.0-clamp(input,-1,1));
}

float3 RotateVectorYaw(float3 vec, float degreeOfRotation)
{
    float3 rotatedVec = vec;
    float angle = radians(degreeOfRotation);

    rotatedVec.x = ( cos(angle) * vec.x ) - ( sin(angle) * vec.z );
    rotatedVec.z = ( sin(angle) * vec.x ) + ( cos(angle) * vec.z );

    return rotatedVec;
}

float3 RotateVectorRoll(float3 vec, float degreeOfRotation)
{
    float3 rotatedVec = vec;
    float angle = radians(degreeOfRotation);

    rotatedVec.y = ( cos(angle) * vec.y ) - ( sin(angle) * vec.z );
    rotatedVec.z = ( sin(angle) * vec.y ) + ( cos(angle) * vec.z );

    return rotatedVec;
}

float3 RotateVectorPitch(float3 vec, float degreeOfRotation)
{
    float3 rotatedVec = vec;
    float angle = radians(degreeOfRotation);

    rotatedVec.x = ( cos(angle) * vec.x ) - ( sin(angle) * vec.y );
    rotatedVec.y = ( sin(angle) * vec.x ) + ( cos(angle) * vec.y );

    return rotatedVec;
}

float3 normalsTangent(float3 normalTexture,
                      float3 Nn,
                      float3 Bn,
                      float3 Tn,
                      bool   invertGreen)
{
  if(invertGreen) invert(normalTexture.g);
  float3 normalValues = normalTexture * 2.0 - 1.0;
  Nn = normalize((normalValues.x*Tn )+(normalValues.y*Bn )+(normalValues.z*Nn ) );

  return Nn;
}

float remap(float value, float low1, float high1, float low2, float high2)
{
    return low2 + (value - low1) * (high2 - low2) / (high1 - low1);
}

float contrast(float value, float contrast)
{
    const float AvgLum = 0.5;
    return lerp(AvgLum, value, contrast);
}

float4 desaturate(float3 color, float Desaturation)
{
    float3 grayXfer = float3(0.3, 0.59, 0.11);
    float grayf = dot(grayXfer, color);
    float3 gray = float3(grayf, grayf, grayf);
    return float4(lerp(color, gray, Desaturation), 1.0);
}

float fresnel (float3 N, float3 V) //this is the most basic approximation of the fresnel function
{
    //return max(0.f,pow(abs(1.0-dot(N,V)),fresnelExp));
    return abs(dot(N,V));
}

//------------------------------------
// Structs
//------------------------------------
struct APPDATA
{
    float3 position     : POSITION;
    float3 normal       : NORMAL;
    float3 binormal     : BINORMAL;
    float3 tangent      : TANGENT;
    float2 UV           : TEXCOORD0;
};

struct SHADERDATA
{
    float4 hPosition        : POSITION;
    float3 worldNormal      : NORMAL;
    float4 worldTangent     : TANGENT;
    float4 worldBinormal    : BINORMAL;
    float2 UV               : TEXCOORD0;
    float3 worldPosition    : TEXCOORD1;
    //float3 cameraLightVec   : TEXCOORD2;
};

//------------------------------------
// vertex shader
//------------------------------------
// take inputs from 3d-app
// vertex animation/skinning would happen here
SHADERDATA v(APPDATA IN)
{
    SHADERDATA OUT = (SHADERDATA)0;

    // we pass vertices in world space
    OUT.worldPosition = mul(float4(IN.position, 1), world).xyz;
    OUT.hPosition = mul( float4(IN.position.xyz, 1), worldViewPrj );

    if(OutputUvSpace)
    {
        float2 uvPos = IN.UV * float2(2,-2) + float2(-1,1);
        uvPos = float2(uvPos.x,(uvPos.y*-1.0));
        OUT.hPosition = float4(uvPos,0,1);
    }

    // Pass through texture coordinates
    // flip Y for Maya
    OUT.UV = float2(IN.UV.x,(1.0-IN.UV.y));

    // output normals in world space:
    OUT.worldNormal = normalize(mul(IN.normal, (float3x3)worldInvXpose));
    // output tangent in world space:
    OUT.worldTangent.xyz = normalize( mul(IN.tangent, (float3x3)worldInvXpose) );
    // store direction for normal map:
    OUT.worldTangent.w = 1;
    if (dot(cross(IN.normal.xyz, IN.tangent.xyz), IN.binormal.xyz) < 0.0) OUT.worldTangent.w = -1;
    // output binormal in world space:
    OUT.worldBinormal.xyz = normalize( mul(IN.binormal, (float3x3)worldInvXpose) );

    //OUT.cameraLightVec = viewInv[3].xyz - OUT.worldPosition.xyz;

    return OUT;
}


float4 f_litSphere(SHADERDATA IN, bool FrontFace : SV_IsFrontFace) : SV_Target
{
    float4x4 viewX = {float4(0.0,0.0,1.0,0.0),
                      float4(0.0,1.0,0.0,0.0),
                      float4(0.0,0.0,0.0,0.0),
                      float4(0.0,0.0,0.0,0.0)};

    float4x4 viewY = {float4(-1.0,0.0,0.0,0.0),
                      float4(0.0,0.0,1.0,0.0),
                      float4(0.0,0.0,0.0,0.0),
                      float4(0.0,0.0,0.0,0.0)};

    float4x4 viewZ = {float4(1.0,0.0,0.0,0.0),
                      float4(0.0,1.0,0.0,0.0),
                      float4(0.0,0.0,0.0,0.0),
                      float4(0.0,0.0,0.0,0.0)};

    float3 V = normalize( viewInv[3].xyz - IN.worldPosition.xyz );
    float3 N = normalize(IN.worldNormal.xyz);
           N = lerp (N, -N, FrontFace);
    float3 T = normalize(IN.worldTangent.xyz);
    float3 Bn = normalize(IN.worldBinormal.xyz);//cross(N, T);

    if (useLitSphereLighten||useLitSphereBlend||useLitSphereCube)
    {
        N = RotateVectorYaw(N, rotateYaw);
        T = RotateVectorYaw(T, rotateYaw);
        Bn = RotateVectorYaw(Bn, rotateYaw);
    }

    if (UseNormalTexture)
    {
        float3 normalTextureSample = NormalTexture.Sample(SamplerAnisoWrap, IN.UV).rgb;
        if(IsSwatchRender == false) N  = normalsTangent(normalTextureSample, N, Bn, T, false);
    }

    float3 Nabs = abs(N);
    float3 Nc = mul(viewInv, float4(N,1)).xyz;
    float3 Nx = mul(viewX, float4(N,1)).xyz;
    float3 Ny = mul(viewY, float4(N,1)).xyz;
    float3 Nz = mul(viewZ, float4(N,1)).xyz;

    float iX = 1;
    float iY = 1;
    if (LitSphereFlipX) iX = -1;
    if (LitSphereFlipY) iY = -1;

    float3 litSphereTextureSample  = LitSphereTexture.Sample(SamplerAnisoWrap, float2(0.49*iX,-0.49*iY) * Nc.xy + 0.5).rgb;
    float3 litSphereTextureSampleX = LitSphereTexture.Sample(SamplerAnisoWrap, float2(0.49*iX,-0.49*iY) * Nx.xy + 0.5).rgb;
    float3 litSphereTextureSampleY = LitSphereTexture.Sample(SamplerAnisoWrap, float2(0.49*iX,-0.49*iY) * Ny.xy + 0.5).rgb;
    float3 litSphereTextureSampleZ = LitSphereTexture.Sample(SamplerAnisoWrap, float2(0.49*iX,-0.49*iY) * Nz.xy + 0.5).rgb;

    litSphereTextureSample  = pow(litSphereTextureSample,  GammaCorrection);
    litSphereTextureSampleX = pow(litSphereTextureSampleX, GammaCorrection);
    litSphereTextureSampleY = pow(litSphereTextureSampleY, GammaCorrection);
    litSphereTextureSampleZ = pow(litSphereTextureSampleZ, GammaCorrection);

    float3 rgbCubeMask = MaskCube.SampleLevel(CubeMapSampler, N, projectionBlend*8).rgb;
    rgbCubeMask = pow(rgbCubeMask, GammaCorrection);

    float3 blend_weights = Nabs;
    blend_weights = blend_weights - 0.577 + projectionBlend;
    blend_weights = max(blend_weights, 0);
    blend_weights /= (blend_weights.x + blend_weights.y + blend_weights.z).xxx;// force sum to 1.0

    float3 col1 = litSphereTextureSampleX;
    float3 col2 = litSphereTextureSampleY;
    float3 col3 = litSphereTextureSampleZ;

    float3 result = litSphereTextureSample;

    if(useLitSphereLighten) result = max(litSphereTextureSampleY, max(litSphereTextureSampleX, litSphereTextureSampleZ));

    if(useLitSphereBlend) result = col1.rgb * blend_weights.xxx + col2.rgb * blend_weights.yyy + col3.rgb * blend_weights.zzz;

    if(useLitSphereCube) result = col1.rgb * rgbCubeMask.zzz + col2.rgb * rgbCubeMask.yyy + col3.rgb * rgbCubeMask.xxx;//my cubemap has x and z switched for some reason

    if(OutputLuminanceOnly) result = desaturate(result,1.0);

    // do gamma correction in shader?
    if (!MayaFullScreenGamma)
        result = pow(result, 1/GammaCorrection);

    return float4(result, 1);
}

float4 f_tri_planar_projection(SHADERDATA IN, bool FrontFace : SV_IsFrontFace) : SV_Target
{
    if (IsSwatchRender) textureScale *= 4;

    float3 N = normalize(IN.worldNormal.xyz);
    float3 Nabs = abs(N);
    float3 blend_weights = Nabs;
    blend_weights = blend_weights - 0.577 + triBlend;
    blend_weights = max(blend_weights, 0);
    // force sum to 1.0
    blend_weights /= (blend_weights.x + blend_weights.y + blend_weights.z).xxx;

    float2 coord1 = IN.worldPosition.yz * textureScale;
    float2 coord2 = IN.worldPosition.zx * textureScale;
    float2 coord3 = IN.worldPosition.xy * textureScale;

    float3 col1 = TilingSphereTexture.Sample(SamplerAnisoWrap, coord1).rgb;
    float3 col2 = TilingSphereTexture.Sample(SamplerAnisoWrap, coord2).rgb;
    float3 col3 = TilingSphereTexture.Sample(SamplerAnisoWrap, coord3).rgb;

    col1 = pow(saturate(col1), GammaCorrection);
    col2 = pow(saturate(col2), GammaCorrection);
    col3 = pow(saturate(col3), GammaCorrection);

    float3 blended_color = col1.rgb * blend_weights.xxx + col2.rgb * blend_weights.yyy + col3.rgb * blend_weights.zzz;

    float3 result = blended_color;

    if (OutputLuminanceOnly) result = desaturate(result,1.0);

    // do gamma correction in shader?
    if (!MayaFullScreenGamma)
        result = pow(result, 1/GammaCorrection);

    return float4(result, 1);
}

//-----------------------------------
// Objects without tessellation
//------------------------------------
RasterizerState FrontFace {
    //FrontCounterClockwise = true;
    CullMode = Front;
};
RasterizerState Backface {
    //FrontCounterClockwise = false;
    CullMode = Back;
};
RasterizerState Noneface {
    //FrontCounterClockwise = false;
    CullMode = None;
};

//------------------------
//Techniques
//------------------------
technique11 Lit_Sphere
<
    bool overridesDrawState = false;    // we do not supply our own render state settings
    int isTransparent = 0;
>
{
    pass p0
    <
        string drawContext = "colorPass";   // tell maya during what draw context this shader should be active, in this case 'Color'
    >
    {
        SetRasterizerState(Backface);
        SetVertexShader(CompileShader(vs_5_0, v()));
        SetHullShader(NULL);
        SetDomainShader(NULL);
        SetGeometryShader(NULL);
        SetPixelShader(CompileShader(ps_5_0, f_litSphere()));

    }
    pass p1
    <
        string drawContext = "colorPass";   // tell maya during what draw context this shader should be active, in this case 'Color'
    >
    {
        SetRasterizerState(FrontFace);
        SetVertexShader(CompileShader(vs_5_0, v()));
        SetHullShader(NULL);
        SetDomainShader(NULL);
        SetGeometryShader(NULL);
        SetPixelShader(CompileShader(ps_5_0, f_litSphere()));

    }
}

technique11 Tri_Planar
<
    bool overridesDrawState = false;    // we do not supply our own render state settings
    int isTransparent = 0;
>
{
    pass p0
    <
        string drawContext = "colorPass";   // tell maya during what draw context this shader should be active, in this case 'Color'
    >
    {
        SetRasterizerState(Backface);
        SetVertexShader(CompileShader(vs_5_0, v()));
        SetHullShader(NULL);
        SetDomainShader(NULL);
        SetGeometryShader(NULL);
        SetPixelShader(CompileShader(ps_5_0, f_tri_planar_projection()));

    }
    pass p1
    <
        string drawContext = "colorPass";   // tell maya during what draw context this shader should be active, in this case 'Color'
    >
    {
        SetRasterizerState(FrontFace);
        SetVertexShader(CompileShader(vs_5_0, v()));
        SetHullShader(NULL);
        SetDomainShader(NULL);
        SetGeometryShader(NULL);
        SetPixelShader(CompileShader(ps_5_0, f_tri_planar_projection()));

    }
}

/////////////////////////////////////// eof //