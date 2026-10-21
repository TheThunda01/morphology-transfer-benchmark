# Glossary

These definitions explain the terms used in this project. Read them alongside the [methods](methods.md) and [assumptions](assumptions.md); a familiar label does not establish a result’s validity.

| Term | Meaning here |
| --- | --- |
| Cell Painting; morphology; phenotype | Cell Painting uses several fluorescent labels and image analysis to summarize cell appearance. Morphology is appearance and organization; a phenotype is an observed property under specified conditions. |
| A549; cell line | A549 is a human lung cancer-derived cultured cell line. A cell line is a maintained laboratory population, not a representative sample of all tissues or patients. |
| LINCS | Library of Integrated Network-based Cellular Signatures, the program associated with these public perturbation profiles. |
| Perturbation; compound; mechanism of action (MOA) | A perturbation changes a system; these experiments use chemical compounds. MOA annotations summarize reported biological actions and can be incomplete or context-dependent. |
| Tubulin; topoisomerase; proteasome; HDAC | Tubulin forms microtubules; topoisomerases alter DNA topology; the proteasome degrades proteins; histone deacetylases remove acetyl groups from histones and other substrates. These are annotation categories, not activities measured here. |
| Kinase; MEK; EGFR; Aurora; PI3K | Kinases transfer phosphate groups. MEK means mitogen-activated protein kinase kinase; EGFR means epidermal growth factor receptor; Aurora names a kinase family; PI3K means phosphoinositide 3-kinase. The dataset supplies inhibitor labels for these categories. |
| Polypharmacology; direct target | A compound can affect multiple molecular targets. A direct target physically interacts with the compound; morphological similarity cannot establish that interaction. |
| Fluorescence; intensity; channel | Fluorescence is emitted light after excitation. Intensity is measured brightness; a channel collects a selected spectral signal. Neither directly measures a specific protein concentration here. |
| DNA; RNA; ER; AGP; Mito | Deoxyribonucleic acid, ribonucleic acid, endoplasmic reticulum, a combined actin/Golgi/plasma-membrane channel, and a mitochondrial channel. Channel names describe stains, not perfectly specific molecular assays. |
| Nucleus; cytoplasm; segmentation mask | The nucleus contains most cellular DNA; cytoplasm is the region outside it. A segmentation mask is an image-defined object boundary used for feature measurements. |
| Well; plate; plate map; batch | A well is one experimental compartment; a plate holds many wells. A plate map specifies their treatment layout. A batch groups measurements sharing preparation or acquisition conditions. |
| Replicate; group; independent unit | Replicates are repeated measurements. This benchmark groups matching supplied compound-connectivity identifiers. Those groups are evaluation units; their biological independence is not established. |
| DMSO; negative control | Dimethyl sulfoxide is the solvent control here. A negative control provides a reference without the annotated treatment; it does not prove that all technical effects have been removed. |
| Dose category; μM; exposure duration | A category orders recorded concentrations; μM means micromoles per liter. Exposure duration is the length of time cells receive the treatment. Conflicting source units remain unresolved; the project does not convert its raw concentration column. |
| InChIKey14; connectivity | The first 14 characters of an International Chemical Identifier hash encode molecular connectivity. This supplied key groups related identities, but is not a full chemical-family or stereochemistry comparison. |
| Feature; vector; multivariate | A feature is one numerical measurement. A vector lists measurements for a sample; multivariate analysis uses several together. |
| Area; perimeter; major/minor axis | Area measures object size in image units, perimeter its boundary length, and the major/minor axes the long/short axes of an equivalent fitted ellipse. |
| Compactness; form factor; eccentricity | Shape descriptors: compactness summarizes shape using a size-adjusted boundary descriptor; form factor compares area with squared perimeter; eccentricity describes ellipse elongation. Upstream CellProfiler definitions govern the stored values. |
| Solidity; extent | Solidity compares object area with its convex hull; extent compares object area with its bounding rectangle. Both summarize shape. |
| Median; standard deviation; MAD | Median is the middle value. Standard deviation summarizes spread around a mean; median absolute deviation is the median distance from the median. MAD ×1.4826 matches a standard deviation under a normal-distribution reference, not for every distribution. |
| Normalization; imputation; standardization | Normalization uses plate controls here. Imputation fills missing values using training medians. Standardization subtracts training means and divides by training standard deviations. |
| Training; validation; test; leakage | Training estimates model parameters; validation chooses settings; test describes fixed choices. Leakage lets information from an evaluation role influence development. |
| Cosine similarity; retrieval; gallery | Cosine similarity compares vector directions. Retrieval ranks reference examples in a gallery for each query; similar direction need not mean equal response size. |
| Precision; recall; average precision (AP) | Precision is the relevant fraction among retrieved examples; recall is the fraction of all relevant examples retrieved. AP weights precision by increases in recall. Tied scores are grouped by the implementation. |
| Mean AP; top-1; macro F1; accuracy | Mean AP averages query AP values; top-1 checks the first match. F1 combines precision and recall, macro F1 averages class F1 equally, and accuracy is the fraction of correct class predictions. |
| Logistic regression; regularization; C | A model using linear scores to predict class probabilities. Regularization constrains fitted coefficients; smaller C means stronger regularization in this implementation. |
| Random forest; tree depth; prior baseline | A random forest combines randomized decision trees; depth limits sequential splits. The prior baseline uses training class frequencies without measured features. |
| Bootstrap; exchangeability; percentile interval | Bootstrap sampling resamples the observed units with replacement. Exchangeability means treating units as interchangeable for this sampling model. Percentile intervals summarize that conditional resampling and omit many other uncertainties. |
| Confounding; transfer; generalization | Confounding mixes biological and technical influences. Transfer/generalization concern predictions in new settings; holding out identities within one panel does not establish transfer to another laboratory. |
| Hash; SHA-256; DVC; snapshot | A hash fingerprints bytes; SHA-256 is one hash algorithm. Data Version Control tracks data objects. A snapshot is a fixed recorded dataset version. |
| CSV; JSON; CLI; CI; seed | Comma-separated values and JavaScript Object Notation are text formats; command-line interface and continuous integration support execution and checks. A seed initializes reproducible pseudorandom choices. |
| MIT; BSD 3-Clause; CC0 | Code licenses and a public-domain dedication. This project’s MIT code does not replace upstream data terms; inspected upstream software has its own license. |
