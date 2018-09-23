<?php
/**
*  @author    Martin Tomasek
*  @copyright DiffSolutions, s.r.o.
*  @license   https://creativecommons.org/licenses/by-sa/4.0/ CC BY-SA 4.0
*/

class XMLW
{
    public function __construct($feedname, $tag, $listTag)
    {
        $this->start($feedname, $tag, $listTag);
    }

    private function start($feedName, $tag, $listTag)
    {
        $this->feedName = $feedName;
        $this->tag = $tag;
        $this->listTag = $listTag;

        $xw = new XMLWriter();
        $this->xw = $xw;
        $xw->openUri($feedName); # php://output is direct output uri to the user
        $xw->setIndent(true);
        $xw->setIndentString(' ');
        $xw->startDocument('1.0', 'UTF-8');
        $xw->startElement($tag);
        $this->open = true;
    }

    public function getWriter()
    {
        return $this->xw;
    }

    public function startLn()
    {
        $this->xw->startElement($this->listTag);
        return $this->xw;
    }

    public function endLn()
    {
        $this->xw->endElement();
    }

    public function end()
    {
        $xw = $this->xw;
        $xw->endElement();
        $xw->endDocument();
        $xw->open = false;
    }

    public function __destruct()
    {
        if ($this->open) {
            $this->end();
        }
    }
}

/*
$wr = new XMLW();
$wr->start("hokus.xml", "HOKUS", "HOKUS_ITEM");
$ln = $wr->newLn();
$ln->startElement('NAME');
$ln->writeCdata('hdshdasdhsjkdashk');
$ln->endElement();
$wr->endLn();
$wr->end();
 */
