from cpyroot.tools.DataMC import DataMCPlot, Histogram
from ROOT import RooRealVar, RooPolynomial, RooConstVar, RooDataSet, RooDataHist, RooHistPdf, RooGaussian, RooArgSet, RooAddPdf, RooArgList, RooFit, SetOwnership, RooAbsArg
from ROOT import RooMsgService
from ROOT import TCanvas


RooMsgService.instance().setSilentMode(True)
RooMsgService.instance().setGlobalKillBelow(RooFit.ERROR)

class BaseFitter(object):

    def __init__(self, plot):
        assert(isinstance(plot, DataMCPlot))
        self.plot = plot
        self._make_underlying_model()
        self._make_dataset()
        self._make_fit_model()
        self._fit()

    def _make_underlying_model(self):
        self.pdfs = {}
        self.yields = {}  # yields are plain floats
        self.ryields = {}  # keep track of roofit objects for memory management
        nbins, xmin, xmax = self.plot.histos[0].GetBinning()
        self.xvar = RooRealVar("x", "x", xmin, xmax)
        self.xvar.setBins(nbins)
        self.pdfs = {}
        self.hists = []
        pdfs = RooArgList()
        yields = RooArgList()
        for compname, comp in self.plot.histosDict.iteritems():
            if comp.weighted.Integral() == 0:
                continue
            assert(isinstance(comp, Histogram))
            hist = RooDataHist(compname, compname, RooArgList(self.xvar),
                               comp.weighted)
            SetOwnership(hist, False)
            # self.hists.append(hist)
            pdf = RooHistPdf(compname, compname,
                             RooArgSet(self.xvar),
                             hist)
            self.pdfs[compname] = pdf
            # self.pdfs[compname].Print()
            pdfs.add(pdf)
            nevts = comp.Integral(xmin=xmin, xmax=xmax)
            nmin = min(0, nevts * (1 - comp.uncertainty))
            nmax = nevts * (1 + comp.uncertainty)
            theyield = RooRealVar('n{}'.format(compname),
                                  'n{}'.format(compname),
                                  nevts,
                                  nmin, nmax)
            self.ryields[compname] = theyield
            self.yields[compname] = nevts
            yields.add(theyield)
            
        self.underlying_model = RooAddPdf('model', 'model',
                                          pdfs, yields)
    def _make_fit_model(self):
        pass
    
    def _make_dataset(self):
        nevents = sum(self.yields.values())
        self.data = self.underlying_model.generate(RooArgSet(self.xvar), nevents)

    def _fit(self):
        self.tresult = self.underlying_model.fitTo(
            self.data,
            RooFit.Extended(),
            RooFit.Save(),
            RooFit.PrintEvalErrors(-1)
        )

    def print_result(self):
        self.tresult.Print()
        yzh = self.ryields['ZH']
        zh_val = yzh.getVal()
        zh_err = yzh.getError()
        percent_unc = zh_err / zh_val * 100.
        print 'ZH yield  = {:8.2f}'.format(zh_val)
        print 'ZH uncert = {:8.2f}%'.format(percent_unc)
        return percent_unc

    def draw_pdfs(self):
        self.pframe = self.xvar.frame()
        for pdf in self.pdfs.values():
            pdf.plotOn(self.pframe)
        self.pframe.Draw()
        
    def draw_data(self):
        self.mframe = self.xvar.frame()
        self.data.plotOn(self.mframe)
        self.underlying_model.plotOn(self.mframe)
        for icomp, compname in enumerate(self.pdfs):
            self.underlying_model.plotOn(self.mframe,
                              RooFit.Components(compname),
                              RooFit.LineColor(icomp+1))
        self.mframe.Draw()
 
        
class TemplateFitter(BaseFitter):
    
    def _make_fit_model(self):
        self.fit_model = self.underlying_model


class BallFitter(BaseFitter):
    
    def _make_fit_model(self):
        p0 = RooRealVar("p0","p0", 100, -10000, 10000);
        p1 = RooRealVar("p1","p1", 100, -10000, 10000);
        p2 = RooRealVar("p2","p2", 100, -10000, 10000);
        p3 = RooRealVar("p3","p3", 100, -10000, 10000);
        bgd = RooPolynomial("bgd", "bgd", self.xvar, RooArgList(p0, p1, p2, p3))               
        
        
