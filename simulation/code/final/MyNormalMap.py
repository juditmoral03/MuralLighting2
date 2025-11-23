import mitsuba as mi
import drjit as dr

#mi.set_variant("llvm_ad_spectral")

class MyNormalMap(mi.BSDF):
    def __init__(self, props):
        mi.BSDF.__init__(self, props)

        # Retrieve the nested BSDF child object
        self.m_nested_bsdf = props.get('bsdf', None)
        if self.m_nested_bsdf is None or not isinstance(self.m_nested_bsdf, mi.BSDF):
            raise RuntimeError("Exactly one BSDF child object must be specified.")

        # Ensure the normal map is a texture
        self.m_normalmap = props.get('normalmap', None)
        if self.m_normalmap is None or not isinstance(self.m_normalmap, mi.Texture):
            raise RuntimeError("A 'normalmap' texture must be specified.")

        # Add all nested components
        self.m_flags = 0
        self.m_components = []
        for i in range(self.m_nested_bsdf.component_count()):
            flags = self.m_nested_bsdf.flags(i)
            self.m_components.append(flags)
            self.m_flags |= flags

    def sample(self, ctx, si, sample1, sample2, active):
        # Sample the nested BSDF with a perturbed shading frame
        perturbed_si = mi.SurfaceInteraction3f(si)
        perturbed_si.sh_frame = self.frame(si, active)
        perturbed_si.wi = perturbed_si.to_local(si.wi)

        #flip wi if perturbed_si becomesa backface
        #flipWi = (perturbed_si.wi.z < 0.0) & (si.wi.z >= 0.0)
        #perturbed_si.wi = dr.select(flipWi, -perturbed_si.wi, perturbed_si.wi)

        bs, weight = self.m_nested_bsdf.sample(ctx, perturbed_si, sample1, sample2, active)

        # Update the active mask based on the weight
        # Symbolic update of the active mask based on weight
        weight_nonzero = mi.unpolarized_spectrum(weight) != 0.0
        weight_nonzero = dr.any(weight_nonzero)
        active = active & weight_nonzero  # Combine active mask with weight non-zero mask

        # Mask out weight where active is false
        weight = dr.select(active, weight, 0.0)  # Symbolic masking using dr.select

        # Transform the sampled 'wo' back to the original frame and verify orientation
        perturbed_wo = perturbed_si.to_world(bs.wo)
        active &= (mi.Frame3f.cos_theta(bs.wo) * 
                mi.Frame3f.cos_theta(perturbed_wo)) > 0.0
        #bs.wo = perturbed_wo
        #print(f"active type: {type(active)}, shape: {active.shape}")
        #print(f"bs.wo type: {type(bs.wo)}, shape: {bs.wo.shape}")
        #print(f"perturbed_wo type: {type(perturbed_wo)}, shape: {perturbed_wo.shape}")
        bs.wo = dr.select(active, perturbed_wo, bs.wo)

        return bs, weight & active

    def eval(self, ctx, si, wo, active):
        # Evaluate nested BSDF with perturbed shading frame
        perturbed_si = mi.SurfaceInteraction3f(si)
        perturbed_si.sh_frame = self.frame(si, active)
        perturbed_si.wi = perturbed_si.to_local(si.wi)
        perturbed_wo = perturbed_si.to_local(wo)

        #flip wi if perturbed_si becomesa backface
        #flipWi = (perturbed_si.wi.z < 0.0) & (si.wi.z >= 0.0)
        #perturbed_si.wi = dr.select(flipWi, -perturbed_si.wi, perturbed_si.wi)

        # Adjust active mask based on cosine terms
        active &= (mi.Frame3f.cos_theta(wo) * 
                mi.Frame3f.cos_theta(perturbed_wo)) > 0.0

        # Evaluate the nested BSDF
        return self.m_nested_bsdf.eval(ctx, perturbed_si, perturbed_wo, active) & active
    
    def pdf(self, ctx, si, wo, active):
        # Evaluate nested BSDF with perturbed shading frame
        perturbed_si = mi.SurfaceInteraction3f(si)
        perturbed_si.sh_frame = self.frame(si, active)
        perturbed_si.wi = perturbed_si.to_local(si.wi)
        perturbed_wo = perturbed_si.to_local(wo)

        #flip wi if perturbed_si becomesa backface
        #flipWi = (perturbed_si.wi.z < 0.0) & (si.wi.z >= 0.0)
        #perturbed_si.wi = dr.select(flipWi, -perturbed_si.wi, perturbed_si.wi)

        # Adjust active mask based on cosine terms
        active &= (mi.Frame3f.cos_theta(wo) * 
                mi.Frame3f.cos_theta(perturbed_wo)) > 0.0

        # Evaluate and return the PDF of the nested BSDF
        return mi.select(active, self.m_nested_bsdf.pdf(ctx, perturbed_si, perturbed_wo, active), 0.0)

    def eval_pdf(self, ctx, si, wo, active):
        # Profiler phase (can be omitted if unnecessary in Python)
        #mi.MaskProfiler.phase(mi.ProfilerPhase.BSDFEvaluate, active)

        # Evaluate nested BSDF with perturbed shading frame
        perturbed_si = mi.SurfaceInteraction3f(si)
        perturbed_si.sh_frame = self.frame(si, active)
        perturbed_si.wi = perturbed_si.to_local(si.wi)
        perturbed_wo = perturbed_si.to_local(wo)

        #flip wi if perturbed_si becomesa backface
        #flipWi = (perturbed_si.wi.z < 0.0) & (si.wi.z >= 0.0)
        #perturbed_si.wi = dr.select(flipWi, -perturbed_si.wi, perturbed_si.wi)

        # Adjust active mask based on cosine terms
        active &= (mi.Frame3f.cos_theta(wo) * 
                mi.Frame3f.cos_theta(perturbed_wo)) > 0.0

        # Evaluate the nested BSDF's eval_pdf
        value, pdf = self.m_nested_bsdf.eval_pdf(ctx, perturbed_si, perturbed_wo, active)

        # Apply the active mask to the output
        value = value & active
        pdf = dr.select(active, pdf, 0.0)

        return value, pdf

    def traverse(self, callback):
        callback.put_parameter('nested_bsdf', self.m_nested_bsdf, mi.ParamFlags.Differentiable)
        callback.put_parameter('normalmap', self.m_normalmap, mi.ParamFlags.Differentiable | mi.ParamFlags.Discontinuous)

    def parameters_changed(self, keys):
        print("🏝️ there is nothing to do here 🏝️")

    def to_string(self):
        return ('MyNormalMap[\n'
                '    nested_bsdf=%s,\n'
                '    normal_map=%s,\n'
                ']' % (self.m_nested_bsdf, self.m_normalmap))

    def frame(self, si, active):
        # Evaluate the normal map texture and scale it to the range [-1, 1]
        n = dr.fma(self.m_normalmap.eval_3(si, active), 2.0, -1.0)

        # Create a new frame and normalize the perturbed normal
        result = mi.Frame3f()
        result.n = dr.normalize(n)

        # Compute the tangent and bitangent vectors
        result.s = dr.normalize(dr.fma(-result.n, dr.dot(result.n, si.dp_du), si.dp_du))
        result.t = dr.cross(result.n, result.s)
        
        return result

    def eval_diffuse_reflectance(self, si, active):
        return self.m_nested_bsdf.eval_diffuse_reflectance(si, active)