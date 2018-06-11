#define NumberOfMipMaps 0
#define PI 3.1415926
#define GammaCorrection 2.2

//------------------------------------
// Per Frame parameters
//------------------------------------
cbuffer UpdatePerFrame : register(b0)
{
	float4x4 worldInvXpose 	: WorldInverseTranspose < string UIWidget = "None"; >;
	float4x4 viewInv 		: ViewInverse 			< string UIWidget = "None"; >;
	float4x4 view			: View					< string UIWidget = "None"; >;
	float4x4 prj			: Projection			< string UIWidget = "None"; >;
	float4x4 viewPrj		: ViewProjection		< string UIWidget = "None"; >;
	float4x4 worldViewPrj	: WorldViewProjection	< string UIWidget = "None"; >;
	float4x4 world 			: World 				< string UIWidget = "None"; >;

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

SamplerState SamplerShadowDepth
{
	Filter = MIN_MAG_MIP_POINT;
	AddressU = Border;
	AddressV = Border;
	BorderColor = float4(1.0f, 1.0f, 1.0f, 1.0f);
};

//------------------------------------
// Textures
//------------------------------------

Texture2D NormalTexture
<
	string UIGroup = "Textures";
	string ResourceName = "";
	string UIWidget = "FilePicker";
	string UIName = "Normal Map";
	string ResourceType = "2D";
	int mipmaplevels = NumberOfMipMaps;
	int UIOrder = 102;
	int UVEditorOrder = 2;
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

	bool UseNormalTexture
	<
		string UIGroup = "Global Properties";
		string UIName = "Normal Map";
		int UIOrder = 202;
	> = true;

	bool useAoSmoothstep
	<
		string UIGroup = "Fast AO Properties";
		string UIName = "Fast AO use Smoothstep";
		int UIOrder = 401;
	> = false;

	float aoAdjustGamma
	<
		string UIGroup = "Fast AO Properties";
		string UIWidget = "Slider";
		float UIMin = 0.0;
		float UIMax = 5.0;
		float UIStep = 0.001;
		string UIName = "Fast AO Contrast";
		int UIOrder = 403;
	> = 1.0;

	float aoAdjustExp
	<
		string UIGroup = "Fast AO Properties";
		string UIWidget = "Slider";
		float UIMin = -5.0;
		float UIMax = 5.0;
		float UIStep = 0.001;
		string UIName = "Fast AO Slide";
		int UIOrder = 404;
	> = 0.0;

	bool useRampSmoothstep
	<
		string UIGroup = "Gradient Ramp Properties";
		string UIName = "Gradient Ramp use Smoothstep";
		int UIOrder = 501;
	> = false;

	float rampAdjustExp
	<
		string UIGroup = "Gradient Ramp Properties";
		string UIWidget = "Slider";
		float UIMin = -5.0;
		float UIMax = 5.0;
		float UIStep = 0.001;
		string UIName = "Gradient Ramp Slide";
		int UIOrder = 503;
	> = 0.0;

	float rampTop
	<
		string UIGroup = "Gradient Ramp Properties";
		string UIWidget = "Slider";
		string UIName = "Gradient Ramp Top";
		int UIOrder = 504;
	> = 10.0;

	float rampBottom
	<
		string UIGroup = "Gradient Ramp Properties";
		string UIWidget = "Slider";
		string UIName = "Gradient Ramp Bottom";
		int UIOrder = 505;
	> = 0.0;

	bool rampHelper
	<
		string UIGroup = "Gradient Ramp Properties";
		string UIName = "Show Ramp Positioning Helper";
		int UIOrder = 506;
	> = false;

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

#define BlendOverlayf(base, blend) 	(base < 0.5 ? (2.0 * base * blend) : (1.0 - 2.0 * (1.0 - base) * (1.0 - blend)))

//------------------------------------
// Structs
//------------------------------------
struct APPDATA
{
	float3 position		: POSITION;
	float3 normal		: NORMAL;
	float3 binormal		: BINORMAL;
	float3 tangent		: TANGENT;
	float2 UV			: TEXCOORD0;
};

struct SHADERDATA
{
	float4 hPosition		: POSITION;
	float3 worldNormal   	: NORMAL;
	float4 worldTangent 	: TANGENT;
	float4 worldBinormal 	: BINORMAL;
	float2 UV	  			: TEXCOORD0;
	float3 worldPosition	: TEXCOORD1;
  	float3 cameraLightVec	: TEXCOORD2;

	//float clipped : CLIPPED;
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

	OUT.cameraLightVec = viewInv[3].xyz - OUT.worldPosition.xyz;

	return OUT;
}

//------------------------------------
// pixel shader
//------------------------------------

float4 f_fastAo(SHADERDATA IN, bool FrontFace : SV_IsFrontFace) : SV_Target
{
	float3 V = normalize( viewInv[3].xyz - IN.worldPosition.xyz );
	float3 N = normalize(IN.worldNormal.xyz);
		   N = lerp (N, -N, FrontFace);
	float3 T = normalize(IN.worldTangent.xyz);
	float3 Bn = normalize(IN.worldBinormal.xyz);//cross(N, T);

	if (UseNormalTexture)
	{
		float3 normalTextureSample = NormalTexture.Sample(SamplerAnisoWrap, IN.UV).rgb;
        if(IsSwatchRender == false) N  = normalsTangent(normalTextureSample, N, Bn, T, false);
	}


	float aoGradient = 0.5 * N.y + 0.5;
	// float posGradient = IN.worldPosition.y;

	float3 gradient = 1.0;

	float aoGradBase = saturate(aoGradient);

	if (aoAdjustExp> 0.0) aoAdjustExp = remap(aoAdjustExp, 0, 5, 1, 5);
	if (aoAdjustExp< 0.0) aoAdjustExp = remap(aoAdjustExp, -5, 0, -5, -1);
	if (aoAdjustExp > 0.0)
	{
		aoGradBase = pow(saturate(aoGradBase), aoAdjustExp);
	}
	if (aoAdjustExp < 0.0)
	{
		aoGradBase = invert(pow(invert(saturate(aoGradBase)), -1*aoAdjustExp));
	}



	if (aoAdjustGamma < 1.0)
	{
		aoGradBase = pow(aoGradBase, aoAdjustGamma);
	}
	else
	{
		aoGradBase = contrast(saturate(aoGradBase), max(1.0, aoAdjustGamma));
	}



	if (useAoSmoothstep)
	{
		aoGradBase = smoothstep(0.0,1.0,aoGradBase);
	}


	gradient = saturate(aoGradBase);

	float3 result = pow(saturate(gradient), GammaCorrection);

	// do gamma correction in shader:
	if (!MayaFullScreenGamma)
		result = pow(result, 1/GammaCorrection);

	return float4(result, 1.0);
}

float4 f_rampGrad(SHADERDATA IN, bool FrontFace : SV_IsFrontFace) : SV_Target
{
	if (IsSwatchRender){
		rampTop = 1.0;
		rampBottom = -1.0;
	}
	float3 V = normalize( viewInv[3].xyz - IN.worldPosition.xyz );
	float3 N = normalize(IN.worldNormal.xyz);
		   N = lerp (N, -N, FrontFace);
	float3 T = normalize(IN.worldTangent.xyz);
	float3 Bn = normalize(IN.worldBinormal.xyz);//cross(N, T);

	if (UseNormalTexture)
	{
		float3 normalTextureSample = NormalTexture.Sample(SamplerAnisoWrap, IN.UV).rgb;
        if(IsSwatchRender == false) N  = normalsTangent(normalTextureSample, N, Bn, T, false);
	}


	float aoGradient = 0.5 * N.y + 0.5;
	float posGradient = IN.worldPosition.y;

	float3 gradient = 1.0;

	float rampGradBase = saturate(remap(posGradient, rampBottom, rampTop, 0, 1));

	if (rampAdjustExp> 0.0) rampAdjustExp = remap(rampAdjustExp, 0, 5, 1, 5);
	if (rampAdjustExp< 0.0) rampAdjustExp = remap(rampAdjustExp, -5, 0, -5, -1);
	if (rampAdjustExp > 0.0)
	{
		rampGradBase = pow(saturate(rampGradBase), rampAdjustExp);
	}
	if (rampAdjustExp < 0.0)
	{
		rampGradBase = invert(pow(invert(saturate(rampGradBase)), -1*rampAdjustExp));
	}

	if (useRampSmoothstep)
	{
		rampGradBase = smoothstep(0.0,1.0,rampGradBase);
	}

	gradient = saturate(rampGradBase);

	if (rampHelper){
		if (posGradient > rampTop || posGradient < rampBottom) gradient = float3(1.0,0.4,0.4);
	}

	float3 result = pow(saturate(gradient), GammaCorrection);

	// do gamma correction in shader:
	if (!MayaFullScreenGamma)
		result = pow(result, 1/GammaCorrection);

	return float4(result, 1.0);
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
technique11 Fast_AO
<
	bool overridesDrawState = false;	// we do not supply our own render state settings
	int isTransparent = 0;
>
{
	pass p0
	<
		string drawContext = "colorPass";	// tell maya during what draw context this shader should be active, in this case 'Color'
	>
	{
		SetRasterizerState(Backface);
		SetVertexShader(CompileShader(vs_5_0, v()));
		SetHullShader(NULL);
		SetDomainShader(NULL);
		SetGeometryShader(NULL);
		SetPixelShader(CompileShader(ps_5_0, f_fastAo()));

	}
	pass p1
	<
		string drawContext = "colorPass";	// tell maya during what draw context this shader should be active, in this case 'Color'
	>
	{
		SetRasterizerState(FrontFace);
		SetVertexShader(CompileShader(vs_5_0, v()));
		SetHullShader(NULL);
		SetDomainShader(NULL);
		SetGeometryShader(NULL);
		SetPixelShader(CompileShader(ps_5_0, f_fastAo()));

	}
}

technique11 Gradient
<
	bool overridesDrawState = false;	// we do not supply our own render state settings
	int isTransparent = 0;
>
{
	pass p0
	<
		string drawContext = "colorPass";	// tell maya during what draw context this shader should be active, in this case 'Color'
	>
	{
		SetRasterizerState(Backface);
		SetVertexShader(CompileShader(vs_5_0, v()));
		SetHullShader(NULL);
		SetDomainShader(NULL);
		SetGeometryShader(NULL);
		SetPixelShader(CompileShader(ps_5_0, f_rampGrad()));

	}
	pass p1
	<
		string drawContext = "colorPass";	// tell maya during what draw context this shader should be active, in this case 'Color'
	>
	{
		SetRasterizerState(FrontFace);
		SetVertexShader(CompileShader(vs_5_0, v()));
		SetHullShader(NULL);
		SetDomainShader(NULL);
		SetGeometryShader(NULL);
		SetPixelShader(CompileShader(ps_5_0, f_rampGrad()));

	}
}

/////////////////////////////////////// eof //